function Test-VMAvailable {
    param (
        $VMName,
        [PSCredential]$Credential
    )
    Invoke-Command -VMName $VMName -ScriptBlock {
        $ErrorOccurred = $false
        do {
            try {
                $ErrorActionPreference = 'Stop'
                Get-VMHost | Out-Null
            }
            catch {
                $ErrorOccurred = $true
            }
        } while ($ErrorOccurred -eq $true)
    } -Credential $Credential -ErrorAction Ignore
    Write-Host "VM $VMName is now online"
}
