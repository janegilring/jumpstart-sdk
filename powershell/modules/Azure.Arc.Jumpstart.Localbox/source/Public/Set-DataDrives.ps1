function Set-DataDrives {
    param (
        $LocalBoxConfig,
        [PSCredential]$Credential
    )
    $VMs = @()
    $VMs += $LocalBoxConfig.MgmtHostConfig.Hostname
    # foreach ($node in $LocalBoxConfig.NodeHostConfig) {
    #     $VMs += $node.Hostname
    # }
    foreach ($VM in $VMs) {
        Invoke-Command -VMName $VM -Credential $Credential -ScriptBlock {

            # Retrieve disk information for disk number 1
            $disk = Get-Disk -Number 1

            # Ensure the disk is online
            if ($disk.IsOffline) {
                Set-Disk -Number 1 -IsOffline $false | Out-Null
                Set-Disk -Number 1 -IsReadOnly $false | Out-Null
            }

            # Initialize the disk only if it hasn't been initialized yet (i.e. PartitionStyle is RAW)
            if ($disk.PartitionStyle -eq 'RAW') {
                Initialize-Disk -Number 1 | Out-Null
            }

            # Check if a partition with drive letter D already exists on disk 1
            $partition = Get-Partition -DiskNumber 1 | Where-Object { $_.DriveLetter -eq 'D' }
            if (-not $partition) {
                # Create a new partition on disk 1 using the maximum size and explicitly assign drive letter D
                New-Partition -DiskNumber 1 -UseMaximumSize -DriveLetter D | Out-Null
            }

            # Retrieve volume info for drive D
            $volume = Get-Volume -DriveLetter D
            # Format the volume only if it is not already formatted (assuming NTFS is desired)
            if (($null -eq $volume.FileSystem) -or ($volume.FileSystem -ne 'NTFS')) {
                Format-Volume -DriveLetter D -FileSystem NTFS -Confirm:$false | Out-Null
            }

        }
    }
}
