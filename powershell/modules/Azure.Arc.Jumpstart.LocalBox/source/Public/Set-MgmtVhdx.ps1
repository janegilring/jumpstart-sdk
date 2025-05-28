function Set-MgmtVhdx {
    param (
        $VMMac,
        $LocalBoxConfig
    )
    $DriveLetter = $($LocalBoxConfig.HostVMPath).Split(':')
    $path = (("\\localhost\") + ($DriveLetter[0] + "$") + ($DriveLetter[1]) + "\" + $($LocalBoxConfig.MgmtHostConfig.Hostname) + ".vhdx")
    Write-Host "Performing offline installation of Hyper-V on $($LocalBoxConfig.MgmtHostConfig.Hostname)"
    Install-WindowsFeature -Vhd $path -Name Hyper-V, RSAT-Hyper-V-Tools, Hyper-V-Powershell -Confirm:$false | Out-Null
    Start-Sleep -Seconds 20

    # Mount VHDX - bunch of kludgey logic in here to deal with different partition layouts on the GUI and Azure Local VHD images
    Write-Host "Mounting VHDX file at $path"
    [string]$MountedDrive = ""
    $partition = Mount-VHD -Path $path -Passthru | Get-Disk | Get-Partition -PartitionNumber 3
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
    if (!$PantherDir) { New-Item -Path ($MountedDrive + ":\Windows\Panther") -ItemType Directory -Force | Out-Null }

    Set-Content -Value $UnattendXML -Path ($MountedDrive + ":\Windows\Panther\Unattend.xml") -Force

    # Creating folder structure on AzSMGMT
    Write-Host "Creating VMs\Base folder structure on $($LocalBoxConfig.MgmtHostConfig.Hostname)"
    New-Item -Path ($MountedDrive + ":\VMs\Base") -ItemType Directory -Force | Out-Null

    # Injecting configs into VMs
    Write-Host "Injecting files into $path"
    Copy-Item -Path "$Env:LocalBoxDir\LocalBox-Config.psd1" -Destination ($MountedDrive + ":\") -Recurse -Force
    Copy-Item -Path $guiVHDXPath -Destination ($MountedDrive + ":\VMs\Base\GUI.vhdx") -Force
    Copy-Item -Path $AzLocalVHDXPath -Destination ($MountedDrive + ":\VMs\Base\AzL-node.vhdx") -Force
    New-Item -Path ($MountedDrive + ":\") -Name "Windows Admin Center" -ItemType Directory -Force | Out-Null
    Copy-Item -Path "$($LocalBoxConfig.Paths["WACDir"])\*.msi" -Destination ($MountedDrive + ":\Windows Admin Center") -Recurse -Force

    # Dismount VHDX
    Write-Host "Dismounting VHDX File at path $path"
    Dismount-VHD $path
}
