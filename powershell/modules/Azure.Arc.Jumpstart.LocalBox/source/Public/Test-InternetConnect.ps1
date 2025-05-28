function Test-InternetConnect {
    $testIP = $LocalBoxConfig.natDNS
    $ErrorActionPreference = "Stop"
    $intConnect = Test-NetConnection -ComputerName $testip -Port 53

    if (!$intConnect.TcpTestSucceeded) {
        throw "Unable to connect to DNS by pinging $($LocalBoxConfig.natDNS) - Network access to this IP is required."
    }
}
