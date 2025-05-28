function Set-DHCPServerOnDC {
    Param (
        $LocalBoxConfig,
        [PSCredential]$domainCred,
        [PSCredential]$localCred
    )
    Invoke-Command -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Credential $localCred -ScriptBlock {
        # Add NIC for VLAN200 for DHCP server (for use with Arc-enabled VMs)
        Add-VMNetworkAdapter -VMName $VMName -Name "VLAN200" -SwitchName $LocalBoxConfig.FabricSwitch -DeviceNaming "On"
        Get-VMNetworkAdapter -VMName $VMName -Name "VLAN200" | Set-VMNetworkAdapterVLAN -Access -VlanId $LocalBoxConfig.AKSVLAN
    }
    Write-Host "Configuring DHCP scope on DHCP server."
    # Set up DHCP scope for Arc resource bridge
    Invoke-Command -VMName $LocalBoxConfig.DCName -Credential $using:domainCred -ArgumentList $LocalBoxConfig -ScriptBlock {
        $LocalBoxConfig = $args[0]

        Write-Host "Configuring NIC settings for $DCName VLAN200"
        $NIC = Get-NetAdapterAdvancedProperty -RegistryKeyWord "HyperVNetworkAdapterName" | Where-Object { $_.RegistryValue -eq "VLAN200" }
        Rename-NetAdapter -name $NIC.name -newname VLAN200 | Out-Null
        New-NetIPAddress -InterfaceAlias VLAN200 -IPAddress $LocalBoxConfig.dcVLAN200IP -PrefixLength ($LocalBoxConfig.AKSIPPrefix.split("/"))[1] -DefaultGateway $LocalBoxConfig.AKSGWIP | Out-Null

        # Install DHCP feature
        Install-WindowsFeature DHCP -IncludeManagementTools
        CMD.exe /c "netsh dhcp add securitygroups"
        Restart-Service dhcpserver

        # Allow DHCP in domain
        $dnsName = $LocalBoxConfig.DCName
        $fqdnsName = $LocalBoxConfig.DCName + "." + $LocalBoxConfig.SDNDomainFQDN
        Add-DhcpServerInDC -DnsName $fqdnsName -IPAddress $LocalBoxConfig.dcVLAN200IP
        Get-DHCPServerInDC

        # Bind DHCP only to VLAN200 NIC
        Set-DhcpServerv4Binding -ComputerName $dnsName -InterfaceAlias $dnsName -BindingState $false
        Set-DhcpServerv4Binding -ComputerName $dnsName -InterfaceAlias VLAN200 -BindingState $true

        # Add DHCP scope for Resource bridge VMs
        Add-DhcpServerv4Scope -name "ResourceBridge" -StartRange $LocalBoxConfig.rbVipStart -EndRange $LocalBoxConfig.rbVipEnd -SubnetMask 255.255.255.0 -State Active
        $scope = Get-DhcpServerv4Scope
        Add-DhcpServerv4ExclusionRange -ScopeID $scope.ScopeID.IPAddressToString -StartRange $LocalBoxConfig.rbDHCPExclusionStart -EndRange $LocalBoxConfig.rbDHCPExclusionEnd
        Set-DhcpServerv4OptionValue -ComputerName $dnsName -ScopeId $scope.ScopeID.IPAddressToString -DnsServer $LocalBoxConfig.SDNLABDNS -Router $LocalBoxConfig.BGPRouterIP_VLAN200.Trim("/24")
    }
}
