function New-AzLocalNodeVM {
    param (
        $Name,
        $VHDXPath,
        $VMSwitch,
        $LocalBoxConfig
    )
    Write-Host "Creating VM $Name"
    # Create disks
    $VHDX1 = New-VHD -ParentPath $VHDXPath -Path "$($LocalBoxConfig.HostVMPath)\$Name.vhdx" -Differencing
    $VHDX2 = New-VHD -Path "$($LocalBoxConfig.HostVMPath)\$Name-Data.vhdx" -SizeBytes 268435456000 -Dynamic

    # Create S2D Storage
    New-VHD -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk1.vhdx" -SizeBytes $LocalBoxConfig.S2D_Disk_Size -Dynamic | Out-Null
    New-VHD -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk2.vhdx" -SizeBytes $LocalBoxConfig.S2D_Disk_Size -Dynamic | Out-Null
    New-VHD -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk3.vhdx" -SizeBytes $LocalBoxConfig.S2D_Disk_Size -Dynamic | Out-Null
    New-VHD -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk4.vhdx" -SizeBytes $LocalBoxConfig.S2D_Disk_Size -Dynamic | Out-Null
    New-VHD -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk5.vhdx" -SizeBytes $LocalBoxConfig.S2D_Disk_Size -Dynamic | Out-Null
    New-VHD -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk6.vhdx" -SizeBytes $LocalBoxConfig.S2D_Disk_Size -Dynamic | Out-Null

    # Create Nested VM
    New-VM -Name $Name -MemoryStartupBytes $LocalBoxConfig.NestedVMMemoryinGB -VHDPath $VHDX1.Path -SwitchName $VMSwitch -Generation 2 | Out-Null
    Add-VMHardDiskDrive -VMName $Name -Path $VHDX2.Path
    Add-VMHardDiskDrive -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk1.vhdx" -VMName $Name | Out-Null
    Add-VMHardDiskDrive -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk2.vhdx" -VMName $Name | Out-Null
    Add-VMHardDiskDrive -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk3.vhdx" -VMName $Name | Out-Null
    Add-VMHardDiskDrive -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk4.vhdx" -VMName $Name | Out-Null
    Add-VMHardDiskDrive -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk5.vhdx" -VMName $Name | Out-Null
    Add-VMHardDiskDrive -Path "$($LocalBoxConfig.HostVMPath)\$Name-S2D_Disk6.vhdx" -VMName $Name | Out-Null

    Set-VM -Name $Name -ProcessorCount 20 -AutomaticStartAction Start -AutomaticStopAction ShutDown -AutomaticStartDelay 300
    Get-VMNetworkAdapter -VMName $Name | Rename-VMNetworkAdapter -NewName "SDN"
    Get-VMNetworkAdapter -VMName $Name | Set-VMNetworkAdapter -DeviceNaming On -StaticMacAddress  ("{0:D12}" -f ( Get-Random -Minimum 0 -Maximum 99999 ))
    # Add-VMNetworkAdapter -VMName $Name -Name SDN2 -DeviceNaming On -SwitchName $VMSwitch
    $vmMac = ((Get-VMNetworkAdapter -Name SDN -VMName $Name).MacAddress) -replace '..(?!$)', '$&-'

    Add-VMNetworkAdapter -VMName $Name -SwitchName $VMSwitch -DeviceNaming On -Name StorageA
    Add-VMNetworkAdapter -VMName $Name -SwitchName $VMSwitch -DeviceNaming On -Name StorageB

    Get-VM $Name | Set-VMProcessor -ExposeVirtualizationExtensions $true
    Get-VM $Name | Set-VMMemory -DynamicMemoryEnabled $false
    Get-VM $Name | Get-VMNetworkAdapter | Set-VMNetworkAdapter -MacAddressSpoofing On

    Set-VMNetworkAdapterVlan -VMName $Name -VMNetworkAdapterName SDN -Trunk -NativeVlanId 0 -AllowedVlanIdList 1-200
    # Set-VMNetworkAdapterVlan -VMName $Name -VMNetworkAdapterName SDN2 -Trunk -NativeVlanId 0 -AllowedVlanIdList 1-200
    Set-VMNetworkAdapterVlan -VMName $Name -VMNetworkAdapterName StorageA -Trunk -NativeVlanId 0 -AllowedVlanIdList 1-800
    Set-VMNetworkAdapterVlan -VMName $Name -VMNetworkAdapterName StorageB -Trunk -NativeVlanId 0 -AllowedVlanIdList 1-800

    Enable-VMIntegrationService -VMName $Name -Name "Guest Service Interface"
    return $vmMac
}
