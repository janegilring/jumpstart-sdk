function Mount-VHDWithRetry {
    param(
        [string]$VhdPath,
        [int]$Retries = 5,
        [int]$DelaySeconds = 5
    )
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            return Mount-VHD -Path $VhdPath -Passthru -ErrorAction Stop
        } catch {
            Write-Warning "Attempt $i to mount VHDX failed: $($_.Exception.Message)"
            if ($i -eq $Retries) {
                throw "Failed to mount VHDX after $Retries attempts."
            }
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}
