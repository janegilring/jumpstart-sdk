function Set-FabricNetwork {
    param (
        $LocalBoxConfig,
        [PSCredential]$localCred
    )
    Start-Sleep -Seconds 20
    Write-Host "Configuring Fabric network on Management VM"
    Invoke-Command -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Credential $localCred -ScriptBlock {
        $localCred = $using:localCred
        $domainCred = $using:domainCred
        $LocalBoxConfig = $using:LocalBoxConfig

        $ErrorActionPreference = "Stop"

        # Disable Fabric2 Network Adapter
        # Write-Host "Disabling Fabric2 Adapter"
        # Get-NetAdapter FABRIC2 | Disable-NetAdapter -Confirm:$false | Out-Null

        # Enable WinRM on AzSMGMT
        Write-Host "Enabling PSRemoting on $env:COMPUTERNAME"
        Set-Item WSMan:\localhost\Client\TrustedHosts * -Confirm:$false -Force
        Enable-PSRemoting | Out-Null

        # Disable ServerManager Auto-Start
        Get-ScheduledTask -TaskName ServerManager | Disable-ScheduledTask | Out-Null

        # Create Hyper-V Networking for AzSMGMT
        Import-Module Hyper-V

        Write-Host "Creating VM Switch on $env:COMPUTERNAME"
        New-VMSwitch -AllowManagementOS $true -Name $LocalBoxConfig.FabricSwitch -NetAdapterName $LocalBoxConfig.FabricNIC -MinimumBandwidthMode None | Out-Null

        Write-Host "Configuring NAT on $env:COMPUTERNAME"
        $Prefix = ($LocalBoxConfig.natSubnet.Split("/"))[1]
        $natIP = ($LocalBoxConfig.natSubnet.TrimEnd("0./$Prefix")) + (".1")
        $provIP = $LocalBoxConfig.BGPRouterIP_ProviderNetwork.TrimEnd("1/24") + "254"
        $vlan200IP = $LocalBoxConfig.BGPRouterIP_VLAN200.TrimEnd("1/24") + "250"
        $vlan110IP = $LocalBoxConfig.BGPRouterIP_VLAN110.TrimEnd("1/24") + "250"
        $provGW = $LocalBoxConfig.BGPRouterIP_ProviderNetwork.TrimEnd("/24")
        $provpfx = $LocalBoxConfig.BGPRouterIP_ProviderNetwork.Split("/")[1]
        $vlan200pfx = $LocalBoxConfig.BGPRouterIP_VLAN200.Split("/")[1]
        $vlan110pfx = $LocalBoxConfig.BGPRouterIP_VLAN110.Split("/")[1]
        $simInternetIP = $LocalBoxConfig.BGPRouterIP_SimulatedInternet.TrimEnd("1/24") + "254"
        $simInternetPFX = $LocalBoxConfig.BGPRouterIP_SimulatedInternet.Split("/")[1]
        New-VMSwitch -SwitchName NAT -SwitchType Internal -MinimumBandwidthMode None | Out-Null
        New-NetIPAddress -IPAddress $natIP -PrefixLength $Prefix -InterfaceAlias "vEthernet (NAT)" | Out-Null
        New-NetNat -Name NATNet -InternalIPInterfaceAddressPrefix $LocalBoxConfig.natSubnet | Out-Null

        Write-Host "Configuring Provider NIC on $env:COMPUTERNAME"
        $NIC = Get-NetAdapterAdvancedProperty -RegistryKeyWord "HyperVNetworkAdapterName" | Where-Object { $_.RegistryValue -eq "PROVIDER" }
        Rename-NetAdapter -name $NIC.name -newname "PROVIDER" | Out-Null
        New-NetIPAddress -InterfaceAlias "PROVIDER" -IPAddress $provIP -PrefixLength $provpfx | Out-Null

        Write-Host "Configuring VLAN200 NIC on $env:COMPUTERNAME"
        $NIC = Get-NetAdapterAdvancedProperty -RegistryKeyWord "HyperVNetworkAdapterName" | Where-Object { $_.RegistryValue -eq "VLAN200" }
        Rename-NetAdapter -name $NIC.name -newname "VLAN200" | Out-Null
        New-NetIPAddress -InterfaceAlias "VLAN200" -IPAddress $vlan200IP -PrefixLength $vlan200pfx | Out-Null

        Write-Host "Configuring VLAN110 NIC on $env:COMPUTERNAME"
        $NIC = Get-NetAdapterAdvancedProperty -RegistryKeyWord "HyperVNetworkAdapterName" | Where-Object { $_.RegistryValue -eq "VLAN110" }
        Rename-NetAdapter -name $NIC.name -newname "VLAN110" | Out-Null
        New-NetIPAddress -InterfaceAlias "VLAN110" -IPAddress $vlan110IP -PrefixLength $vlan110pfx | Out-Null

        Write-Host "Configuring simulatedInternet NIC on $env:COMPUTERNAME"
        $NIC = Get-NetAdapterAdvancedProperty -RegistryKeyWord "HyperVNetworkAdapterName" | Where-Object { $_.RegistryValue -eq "simInternet" }
        Rename-NetAdapter -name $NIC.name -newname "simInternet" | Out-Null
        New-NetIPAddress -InterfaceAlias "simInternet" -IPAddress $simInternetIP -PrefixLength $simInternetPFX | Out-Null

        Write-Host "Configuring NAT"
        $NIC = Get-NetAdapterAdvancedProperty -RegistryKeyWord "HyperVNetworkAdapterName" | Where-Object { $_.RegistryValue -eq "Network Adapter" -or $_.RegistryValue -eq "NAT" }
        Rename-NetAdapter -name $NIC.name -newname "Internet" | Out-Null
        $internetIP = $LocalBoxConfig.natHostSubnet.Replace("0/24", "5")
        $internetGW = $LocalBoxConfig.natHostSubnet.Replace("0/24", "1")
        Start-Sleep -Seconds 15
        $internetIndex = (Get-NetAdapter | Where-Object { $_.Name -eq "Internet" }).ifIndex
        Start-Sleep -Seconds 15
        New-NetIPAddress -IPAddress $internetIP -PrefixLength 24 -InterfaceIndex $internetIndex -DefaultGateway $internetGW -AddressFamily IPv4 | Out-Null
        Set-DnsClientServerAddress -InterfaceIndex $internetIndex -ServerAddresses ($LocalBoxConfig.natDNS) | Out-Null

        # Provision Public and Private VIP Route
        New-NetRoute -DestinationPrefix $LocalBoxConfig.PublicVIPSubnet -NextHop $provGW -InterfaceAlias PROVIDER | Out-Null

        # Remove Gateway from Fabric NIC
        Write-Host "Removing Gateway from Fabric NIC"
        $index = (Get-WmiObject Win32_NetworkAdapter | Where-Object { $_.netconnectionid -match "vSwitch-Fabric" }).InterfaceIndex
        Remove-NetRoute -InterfaceIndex $index -DestinationPrefix "0.0.0.0/0" -Confirm:$false
    }
}
