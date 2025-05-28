function Set-HostNAT {
    param (
        $LocalBoxConfig
    )

    $switchExist = Get-NetAdapter | Where-Object { $_.Name -match $LocalBoxConfig.natHostVMSwitchName }
    if (!$switchExist) {
        Write-Host "Creating NAT Switch: $($LocalBoxConfig.natHostVMSwitchName)"
        # Create Internal VM Switch for NAT
        New-VMSwitch -Name $LocalBoxConfig.natHostVMSwitchName -SwitchType Internal | Out-Null

        Write-Host "Applying IP Address to NAT Switch: $($LocalBoxConfig.natHostVMSwitchName)"
        # Apply IP Address to new Internal VM Switch
        $intIdx = (Get-NetAdapter | Where-Object { $_.Name -match $LocalBoxConfig.natHostVMSwitchName }).ifIndex
        $natIP = $LocalBoxConfig.natHostSubnet.Replace("0/24", "1")
        New-NetIPAddress -IPAddress $natIP -PrefixLength 24 -InterfaceIndex $intIdx | Out-Null

        # Create NetNAT
        Write-Host "Creating new Net NAT"
        New-NetNat -Name $LocalBoxConfig.natHostVMSwitchName  -InternalIPInterfaceAddressPrefix $LocalBoxConfig.natHostSubnet | Out-Null
    }
}
