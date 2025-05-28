function Wait-AzureEdgeBootstrap {
    param (
        [string]$VMName,
        [PSCredential]$Credential,
        [int]$TimeoutSeconds = 300,
        [int]$RetryIntervalSeconds = 10
    )

    $pathsToCheck = @(
        'C:\Windows\System32\WindowsPowerShell\v1.0\Modules\AzureEdgeBootstrap',
        'C:\Program Files\WindowsPowerShell\Modules\Az.Accounts'
    )

    $scriptBlock = {
        param($paths, $timeout, $interval)

        $elapsed = 0

        while ($true) {
            $status = foreach ($path in $paths) {
                $exists = Test-Path $path
                [PSCustomObject]@{
                    Path   = $path
                    Exists = $exists
                }
            }

            $missing = $status | Where-Object { -not $_.Exists }

            Write-Host "🔍 Path check status at $((Get-Date).ToString("HH:mm:ss")):"
            foreach ($entry in $status) {
                if ($entry.Exists) {
                    Write-Host "✅ $($entry.Path)"
                } else {
                    Write-Host "❌ $($entry.Path)"
                }
            }

            if (-not $missing) {
                Write-Host "✅ All required paths found. Continuing."
                break
            }

            Start-Sleep -Seconds $interval
            $elapsed += $interval

            if ($elapsed -ge $timeout) {
                $missingPaths = $missing.Path -join ', '
                throw "❌ Timeout waiting for required paths: $missingPaths"
            }
        }
    }

    Invoke-Command -VMName $VMName -Credential $Credential -ScriptBlock $scriptBlock -ArgumentList $pathsToCheck, $TimeoutSeconds, $RetryIntervalSeconds
}
