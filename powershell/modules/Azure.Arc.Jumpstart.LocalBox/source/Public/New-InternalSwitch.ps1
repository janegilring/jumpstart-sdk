function New-InternalSwitch {
    param (
        $LocalBoxConfig
    )
    $pswitchname = $LocalBoxConfig.InternalSwitch
    $querySwitch = Get-VMSwitch -Name $pswitchname -ErrorAction Ignore
    if (!$querySwitch) {
        New-VMSwitch -SwitchType Internal -MinimumBandwidthMode None -Name $pswitchname | Out-Null

        #Assign IP to Internal Switch
        $InternalAdapter = Get-Netadapter -Name "vEthernet ($pswitchname)"
        $IP = $LocalBoxConfig.PhysicalHostInternalIP
        $Prefix = ($($LocalBoxConfig.MgmtHostConfig.IP).Split("/"))[1]
        $Gateway = $LocalBoxConfig.SDNLABRoute
        $DNS = $LocalBoxConfig.SDNLABDNS

        $params = @{
            AddressFamily  = "IPv4"
            IPAddress      = $IP
            PrefixLength   = $Prefix
            DefaultGateway = $Gateway
        }

        $InternalAdapter | New-NetIPAddress @params | Out-Null
        $InternalAdapter | Set-DnsClientServerAddress -ServerAddresses $DNS | Out-Null
    }
    else {
        Write-Host "Internal Switch $pswitchname already exists. Not creating a new internal switch."
    }
}
