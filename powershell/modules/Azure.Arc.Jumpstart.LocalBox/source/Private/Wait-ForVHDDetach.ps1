function Wait-ForVHDDetach {
    param (
        [string]$Path,
        [int]$TimeoutSeconds = 120
    )
    $elapsed = 0
    while ($true) {
        $vhdInfo = Get-VHD -Path $Path -ErrorAction SilentlyContinue
        if (-not $vhdInfo -or -not $vhdInfo.Attached) {
            Write-Host "VHDX at path $Path is no longer attached."
            break
        }
        if ($elapsed -ge $TimeoutSeconds) {
            throw "Timeout waiting for VHDX at path $Path to detach."
        }
        Start-Sleep -Seconds 3
        $elapsed += 3
    }
}
