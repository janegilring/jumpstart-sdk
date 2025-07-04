function Set-AzLocalNodeVhdx {
    param (
        $Hostname,
        $IPAddress,
        $VMMac,
        $LocalBoxConfig
    )

    # Build LOCAL path instead of SMB path
    $DriveLetter = $($LocalBoxConfig.HostVMPath).Split(':')
    $path = $DriveLetter[0] + ":\"  + ($DriveLetter[1].TrimStart('\')) + "\" + $Hostname + ".vhdx"

    Write-Host "Performing offline installation of Hyper-V on $Hostname"
    Install-WindowsFeature -Vhd $path -Name Hyper-V, RSAT-Hyper-V-Tools, Hyper-V-Powershell -Confirm:$false | Out-Null

    Start-Sleep -Seconds 10

    # Ensure VHD is not still attached
    Write-Host "Waiting for VHDX to detach after Install-WindowsFeature..."
    Wait-ForVHDDetach -Path $path

    # Install necessary tools to converge cluster
    Write-Host "Installing and Configuring Failover Clustering on $Hostname"
    Install-WindowsFeature -Vhd $path -Name Failover-Clustering -IncludeAllSubFeature -IncludeManagementTools | Out-Null

    Start-Sleep -Seconds 15

    # Check again in case clustering installation mounted it
    Write-Host "Waiting for VHDX to detach after Install-WindowsFeature..."
    Wait-ForVHDDetach -Path $path

    # Mount VHDX with retry logic
    Write-Host "Mounting VHDX file at $path"
    $vhd = Mount-VHDWithRetry -VhdPath $path
    $disk = $vhd | Get-Disk
    $partition = $disk | Get-Partition -PartitionNumber 3

    if (!$partition.DriveLetter) {
        $MountedDrive = "Y"
        $partition | Set-Partition -NewDriveLetter $MountedDrive
    }
    else {
        $MountedDrive = $partition.DriveLetter
    }

    # Inject Answer File
    Write-Host "Injecting answer file to $path"
    $UnattendXML = GenerateAnswerFile -HostName $Hostname -IPAddress $IPAddress -VMMac $VMMac -LocalBoxConfig $LocalBoxConfig
    Write-Host "Mounted Disk Volume is: $MountedDrive"
    $PantherDir = Get-ChildItem -Path ($MountedDrive + ":\Windows")  -Filter "Panther"
    if (!$PantherDir) {
        New-Item -Path ($MountedDrive + ":\Windows\Panther") -ItemType Directory -Force | Out-Null
    }
    Set-Content -Value $UnattendXML -Path ($MountedDrive + ":\Windows\Panther\Unattend.xml") -Force

    New-Item -Path ($MountedDrive + ":\VHD") -ItemType Directory -Force | Out-Null
    Copy-Item -Path "$($LocalBoxConfig.Paths.VHDDir)" -Destination ($MountedDrive + ":\VHD") -Recurse -Force

    # Dismount VHDX
    Write-Host "Dismounting VHDX File at path $path"
    Dismount-VHD -Path $path

    Write-Host "Waiting for VHDX to detach after injecting answer-file..."
    Wait-ForVHDDetach -Path $path
}
