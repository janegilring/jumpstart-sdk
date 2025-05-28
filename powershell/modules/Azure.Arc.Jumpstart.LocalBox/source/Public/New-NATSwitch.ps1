function New-NATSwitch {
    Param (
        $LocalBoxConfig
    )
    Write-Host "Creating NAT Switch on switch $($LocalBoxConfig.InternalSwitch)"
    Add-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -DeviceNaming On
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname | Where-Object { $_.Name -match "Network" } | Connect-VMNetworkAdapter -SwitchName $LocalBoxConfig.natHostVMSwitchName
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname | Where-Object { $_.Name -match "Network" } | Rename-VMNetworkAdapter -NewName "NAT"
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name NAT | Set-VMNetworkAdapter -MacAddressSpoofing On

    Add-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name PROVIDER -DeviceNaming On -SwitchName $LocalBoxConfig.InternalSwitch
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name PROVIDER | Set-VMNetworkAdapter -MacAddressSpoofing On
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name PROVIDER | Set-VMNetworkAdapterVlan -Access -VlanId $LocalBoxConfig.providerVLAN | Out-Null

    #Create VLAN 110 NIC in order for NAT to work from L3 Connections
    Add-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name VLAN110 -DeviceNaming On -SwitchName $LocalBoxConfig.InternalSwitch
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name VLAN110 | Set-VMNetworkAdapter -MacAddressSpoofing On
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name VLAN110 | Set-VMNetworkAdapterVlan -Access -VlanId $LocalBoxConfig.vlan110VLAN | Out-Null

    #Create VLAN 200 NIC in order for NAT to work from L3 Connections
    Add-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name VLAN200 -DeviceNaming On -SwitchName $LocalBoxConfig.InternalSwitch
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name VLAN200 | Set-VMNetworkAdapter -MacAddressSpoofing On
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name VLAN200 | Set-VMNetworkAdapterVlan -Access -VlanId $LocalBoxConfig.vlan200VLAN | Out-Null

    #Create Simulated Internet NIC in order for NAT to work from L3 Connections
    Add-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name simInternet -DeviceNaming On -SwitchName $LocalBoxConfig.InternalSwitch
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name simInternet | Set-VMNetworkAdapter -MacAddressSpoofing On
    Get-VMNetworkAdapter -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Name simInternet | Set-VMNetworkAdapterVlan -Access -VlanId $LocalBoxConfig.simInternetVLAN | Out-Null
}
