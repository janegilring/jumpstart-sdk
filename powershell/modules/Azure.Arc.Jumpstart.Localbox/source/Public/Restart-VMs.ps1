function Restart-VMs {
    Param (
        $LocalBoxConfig,
        [PSCredential]$Credential
    )
    foreach ($VM in $LocalBoxConfig.NodeHostConfig) {
        Write-Host "Restarting VM: $($VM.Hostname)"
        # Invoke-Command -VMName $VM.Hostname -Credential $Credential -ScriptBlock {
        #     Restart-Computer -Force
        # }
        # Restart via host to avoid "Failed to restart the computer with the following error message: Class not registered"
        Restart-VM -Name $VM.Hostname -Force
    }
    Write-Host "Restarting VM: $($LocalBoxConfig.MgmtHostConfig.Hostname)"

    Restart-VM -Name $LocalBoxConfig.MgmtHostConfig.Hostname -Force
    Start-Sleep -Seconds 30

}
