    function Update-AzDeploymentProgressTag {
        param (
            [Parameter(Mandatory = $true)]
            [string]$ProgressString,
            [Parameter(Mandatory = $true)]
            [string]$ResourceGroupName,
            [Parameter(Mandatory = $true)]
            [string]$ComputerName
        )

        $tags = Get-AzResourceGroup -Name $ResourceGroupName | Select-Object -ExpandProperty Tags

        if ($null -ne $tags) {
            $tags['DeploymentProgress'] = $ProgressString
        } else {
            $tags = @{'DeploymentProgress' = $ProgressString }
        }

        $null = Set-AzResourceGroup -ResourceGroupName $ResourceGroupName -Tag $tags
        $null = Set-AzResource -ResourceName $ComputerName -ResourceGroupName $ResourceGroupName -ResourceType 'microsoft.compute/virtualmachines' -Tag $tags -Force
    }