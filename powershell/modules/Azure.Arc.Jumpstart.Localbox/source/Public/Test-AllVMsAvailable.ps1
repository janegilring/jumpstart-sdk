function Test-AllVMsAvailable
 {
    param (
        $LocalBoxConfig,
        [PSCredential]$Credential
    )
    Write-Host "Testing whether VMs are available..."
    Test-VMAvailable -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Credential $Credential
    foreach ($VM in $LocalBoxConfig.NodeHostConfig) {
        Test-VMAvailable -VMName $VM.Hostname -Credential $Credential
    }
}
