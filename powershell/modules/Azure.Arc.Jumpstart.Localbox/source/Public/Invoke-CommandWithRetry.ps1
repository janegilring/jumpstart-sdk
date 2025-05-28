function Invoke-CommandWithRetry {
    param (
        [string]$VMName,
        [pscredential]$Credential,
        [scriptblock]$ScriptBlock,
        [int]$MaxRetries = 5,
        [int]$RetryDelay = 10
    )

    $retryCount = 0
    $success = $false

    do {
        try {
            Write-Host "Attempt $($retryCount + 1) to execute command on $VMName..."
            Invoke-Command -VMName $VMName -Credential $Credential -ScriptBlock $ScriptBlock -ErrorAction Stop
            $success = $true
            Write-Host "Command executed successfully on $VMName."
        } catch {
            Write-Warning "Failed to execute command on $VMName. Error: $_"
            $retryCount++
            if ($retryCount -lt $MaxRetries) {
                Write-Host "Retrying in $RetryDelay seconds..."
                Start-Sleep -Seconds $RetryDelay
            } else {
                Write-Error "Maximum retries ($MaxRetries) reached. Unable to execute command on $VMName."
            }
        }
    } while (-not $success -and $retryCount -lt $MaxRetries)
}
