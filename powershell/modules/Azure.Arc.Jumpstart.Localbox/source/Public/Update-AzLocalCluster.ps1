function Update-AzLocalCluster {
    param (
        $LocalBoxConfig,
        [PSCredential]$domainCred
    )

    $session = New-PSSession -VMName $LocalBoxConfig.NodeHostConfig[0].Hostname -Credential $domainCred

    Write-Host "Getting current version of the cluster"

    Invoke-Command -Session $session -ScriptBlock {

        Get-StampInformation | Select-Object StampVersion,ServicesVersion,InitialDeployedVersion

    }

    Write-Host "Test environment readiness for update"

    Invoke-Command -Session $session -ScriptBlock {

        Test-EnvironmentReadiness | Select-Object Name,Status,Severity

    }

    Write-Host "Getting available updates"

    Invoke-Command -Session $session -ScriptBlock {

        Get-SolutionUpdate | Select-Object DisplayName, State

    } -OutVariable updates

    if ($updates.Count -gt 0) {

    Write-Host "Starting update process"

        Invoke-Command -Session $session -ScriptBlock {

            Get-SolutionUpdate | Start-SolutionUpdate

            }

    }
    else {

        Write-Host "No updates available"
        return

    }

    Invoke-Command -Session $session -ScriptBlock {

        Get-SolutionUpdate | Select-Object Version,State,UpdateStateProperties,HealthState

    }

    $session | Remove-PSSession

}
