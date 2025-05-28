function Set-AzLocalNodeVhdx {
    param (
        $Hostname,
        $IPAddress,
        $VMMac,
        $LocalBoxConfig
    )
    $DriveLetter = $($LocalBoxConfig.HostVMPath).Split(':')
    $path = (("\\localhost\") + ($DriveLetter[0] + "$") + ($DriveLetter[1]) + "\" + $Hostname + ".vhdx")
    Write-Host "Performing offline installation of Hyper-V on $Hostname"
    Install-WindowsFeature -Vhd $path -Name Hyper-V, RSAT-Hyper-V-Tools, Hyper-V-Powershell -Confirm:$false | Out-Null
    Start-Sleep -Seconds 5

    # Install necessary tools to converge cluster
    Write-Host "Installing and Configuring Failover Clustering on $Hostname"
    Install-WindowsFeature -Vhd $path -Name Failover-Clustering -IncludeAllSubFeature -IncludeManagementTools | Out-Null
    Start-Sleep -Seconds 15

    Write-Host "Mounting VHDX file at $path"
    $partition = Mount-VHD -Path $path -Passthru | Get-Disk | Get-Partition -PartitionNumber 3
    if (!$partition.DriveLetter) {
        $MountedDrive = "Y"
        $partition | Set-Partition -NewDriveLetter $MountedDrive
    }
    else {
        $MountedDrive = $partition.DriveLetter
    }

    Write-Host "Injecting answer file to $path"
    $UnattendXML = GenerateAnswerFile -HostName $Hostname -IPAddress $IPAddress -VMMac $VMMac -LocalBoxConfig $LocalBoxConfig
    Write-Host "Mounted Disk Volume is: $MountedDrive"
    $PantherDir = Get-ChildItem -Path ($MountedDrive + ":\Windows")  -Filter "Panther"
    if (!$PantherDir) { New-Item -Path ($MountedDrive + ":\Windows\Panther") -ItemType Directory -Force | Out-Null }
    Set-Content -Value $UnattendXML -Path ($MountedDrive + ":\Windows\Panther\Unattend.xml") -Force

    New-Item -Path ($MountedDrive + ":\VHD") -ItemType Directory -Force | Out-Null
    Copy-Item -Path "$($LocalBoxConfig.Paths.VHDDir)" -Destination ($MountedDrive + ":\VHD") -Recurse -Force
    # Copy-Item -Path "$($LocalBoxConfig.Paths.VHDDir)\Ubuntu.vhdx" -Destination ($MountedDrive + ":\VHD") -Recurse -Force

    # Dismount VHDX
    Write-Host "Dismounting VHDX File at path $path"
    Dismount-VHD $path
}
