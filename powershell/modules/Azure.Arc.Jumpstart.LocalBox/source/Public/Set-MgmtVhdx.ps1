function Set-MgmtVhdx {
    param (
        $VMMac,
        $LocalBoxConfig
    )

    # Build LOCAL path instead of SMB path
    $DriveLetter = $($LocalBoxConfig.HostVMPath).Split(':')
    $path = $DriveLetter[0] + ":\" + ($DriveLetter[1].TrimStart('\')) + "\" + $($LocalBoxConfig.MgmtHostConfig.Hostname) + ".vhdx"

    Write-Host "Performing offline installation of Hyper-V on $($LocalBoxConfig.MgmtHostConfig.Hostname)"
    Install-WindowsFeature -Vhd $path -Name Hyper-V, RSAT-Hyper-V-Tools, Hyper-V-Powershell -Confirm:$false | Out-Null

    # Wait for DISM and any file handles to close
    Start-Sleep -Seconds 30

    # Check if the VHDX is still attached
    $vhdInfo = Get-VHD -Path $path -ErrorAction SilentlyContinue
    if ($vhdInfo -and $vhdInfo.Attached) {
        Write-Host "VHDX is still attached after Install-WindowsFeature. Dismounting..."
        Dismount-VHD -Path $path
        Start-Sleep -Seconds 5
    }

    # Mount VHDX with retry logic
    Write-Host "Mounting VHDX file at $path"
    $vhd = Mount-VHDWithRetry -VhdPath $path
    $disk = $vhd | Get-Disk
    $partition = $disk | Get-Partition -PartitionNumber 3

    [string]$MountedDrive = ""
    if (!$partition.DriveLetter) {
        $MountedDrive = "X"
        $partition | Set-Partition -NewDriveLetter $MountedDrive
    }
    else {
        $MountedDrive = $partition.DriveLetter
    }

    # Inject Answer File
    Write-Host "Injecting answer file to $path"
    $UnattendXML = GenerateAnswerFile -HostName $($LocalBoxConfig.MgmtHostConfig.Hostname) -IsMgmtVM $true -IPAddress $LocalBoxConfig.MgmtHostConfig.IP -VMMac $VMMac -LocalBoxConfig $LocalBoxConfig

    Write-Host "Mounted Disk Volume is: $MountedDrive"
    $PantherDir = Get-ChildItem -Path ($MountedDrive + ":\Windows")  -Filter "Panther"
    if (!$PantherDir) {
        New-Item -Path ($MountedDrive + ":\Windows\Panther") -ItemType Directory -Force | Out-Null
    }

    Set-Content -Value $UnattendXML -Path ($MountedDrive + ":\Windows\Panther\Unattend.xml") -Force

    # Creating folder structure on AzSMGMT
    Write-Host "Creating VMs\Base folder structure on $($LocalBoxConfig.MgmtHostConfig.Hostname)"
    New-Item -Path ($MountedDrive + ":\VMs\Base") -ItemType Directory -Force | Out-Null

    # Injecting configs into VMs
    Write-Host "Injecting files into $path"
    Copy-Item -Path "$Env:LocalBoxDir\LocalBox-Config.psd1" -Destination ($MountedDrive + ":\") -Recurse -Force
    Copy-Item -Path $LocalBoxConfig.guiVHDXPath -Destination ($MountedDrive + ":\VMs\Base\GUI.vhdx") -Force
    Copy-Item -Path $LocalBoxConfig.AzLocalVHDXPath -Destination ($MountedDrive + ":\VMs\Base\AzL-node.vhdx") -Force
    New-Item -Path ($MountedDrive + ":\") -Name "Windows Admin Center" -ItemType Directory -Force | Out-Null
    Copy-Item -Path "$($LocalBoxConfig.Paths["WACDir"])\*.msi" -Destination ($MountedDrive + ":\Windows Admin Center") -Recurse -Force

    # Dismount VHDX
    Write-Host "Dismounting VHDX File at path $path"
    Dismount-VHD -Path $path
}
