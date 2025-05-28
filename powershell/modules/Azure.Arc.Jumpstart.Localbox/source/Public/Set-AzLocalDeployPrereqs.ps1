function Set-AzLocalDeployPrereqs {
    param (
        $LocalBoxConfig,
        [PSCredential]$localCred,
        [PSCredential]$domainCred
    )
    Invoke-Command -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Credential $localCred -ScriptBlock {
        $LocalBoxConfig = $using:LocalBoxConfig
        $localCred = $using:localcred
        $domainCred = $using:domainCred
        Invoke-Command -VMName $LocalBoxConfig.DCName -Credential $domainCred -ArgumentList $LocalBoxConfig -ScriptBlock {
            $LocalBoxConfig = $args[0]
            $domainCredNoDomain = new-object -typename System.Management.Automation.PSCredential `
                -argumentlist ($LocalBoxConfig.LCMDeployUsername), (ConvertTo-SecureString $LocalBoxConfig.SDNAdminPassword -AsPlainText -Force)

            Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser
            Install-Module AsHciADArtifactsPreCreationTool -Repository PSGallery -Force -Confirm:$false
            $domainName = $LocalBoxConfig.SDNDomainFQDN.Split('.')
            $ouName = "OU=$($LocalBoxConfig.LCMADOUName)"
            foreach ($name in $domainName) {
                $ouName += ",DC=$name"
            }
            $nodes = @()
            foreach ($node in $LocalBoxConfig.NodeHostConfig) {
                $nodes += $node.Hostname.ToString()
            }
            Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))
            New-HciAdObjectsPreCreation -AzureStackLCMUserCredential $domainCredNoDomain -AsHciOUName $ouName
        }
    }

    $armtoken = ConvertFrom-SecureStringToPlainText -SecureString ((Get-AzAccessToken -AsSecureString).Token)
    $clientId = (Get-AzContext).Account.Id
    foreach ($node in $LocalBoxConfig.NodeHostConfig) {
        Invoke-Command -VMName $node.Hostname -Credential $localCred -ArgumentList $env:subscriptionId, $env:tenantId, $clientId, $armtoken, $env:resourceGroup, $env:azureLocation -ScriptBlock {
            $subId = $args[0]
            $tenantId = $args[1]
            $clientId = $args[2]
            $armtoken = $args[3]
            $resourceGroup = $args[4]
            $location = $args[5]

            function ConvertFrom-SecureStringToPlainText {
                param (
                    [Parameter(Mandatory = $true)]
                    [System.Security.SecureString]$SecureString
                )

                $Ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureString)
                try {
                    return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)
                }
                finally {
                    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Ptr)
                }
            }

            # Prep nodes for Azure Arc onboarding
            #winrm quickconfig -quiet
            #netsh advfirewall firewall add rule name="ICMP Allow incoming V4 echo request" protocol=icmpv4:8,any dir=in action=allow

            # Register PSGallery as a trusted repo
            #Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
            #Register-PSRepository -Default -InstallationPolicy Trusted -ErrorAction SilentlyContinue
            #Set-PSRepository -Name PSGallery -InstallationPolicy Trusted

            #Install Arc registration script from PSGallery
            #Install-Module AzsHCI.ARCinstaller -Force # Pre-installed in 24H2 base image, part of module AzureEdgeBootstrap

            #Install required PowerShell modules in your node for registration
            #Install-Module Az.Accounts -Force # Pre-installed in 24H2 base image
            #Install-Module Az.ConnectedMachine -Force
            #Install-Module Az.Resources -Force

            # Workaround for BITS transfer issue
            #Get-NetAdapter StorageA | Disable-NetAdapter -Confirm:$false | Out-Null
            #Get-NetAdapter StorageB | Disable-NetAdapter -Confirm:$false | Out-Null

            #Invoke the registration script.
            Invoke-AzStackHciArcInitialization -SubscriptionID $subId -ResourceGroup $resourceGroup -TenantID $tenantId -Region $location -Cloud "AzureCloud" -ArmAccessToken $armtoken -AccountID $clientId -ErrorAction Continue

            #Get-NetAdapter StorageA | Enable-NetAdapter -Confirm:$false | Out-Null
            #Get-NetAdapter StorageB | Enable-NetAdapter -Confirm:$false | Out-Null
        }
    }

<#     Not needed in 24H2, extensions are installed by cluster validation stage

        Get-AzConnectedMachine -ResourceGroupName $env:resourceGroup | foreach-object {

        Write-Host "Checking extension status for $($PSItem.Name)"

        $requiredExtensions = @('AzureEdgeTelemetryAndDiagnostics', 'AzureEdgeDeviceManagement', 'AzureEdgeLifecycleManager')
        $attempts = 0
        $maxAttempts = 90

        do {
            $attempts++
            $extension = Get-AzConnectedMachineExtension -MachineName $PSItem.Name -ResourceGroupName $env:resourceGroup

            foreach ($extensionName in $requiredExtensions) {
                $extensionTest = $extension | Where-Object { $_.Name -eq $extensionName }
                if (!$extensionTest) {
                    Write-Host "$($PSItem.Name) : Extension $extensionName is missing" -ForegroundColor Yellow
                    $Wait = $true
                } elseif ($extensionTest.ProvisioningState -ne "Succeeded") {
                    Write-Host "$($PSItem.Name) : Extension $extensionName is in place, but not yet provisioned. Current state: $($extensionTest.ProvisioningState)" -ForegroundColor Yellow
                    $Wait = $true
                } elseif ($extensionTest.ProvisioningState -eq "Succeeded") {
                    Write-Host "$($PSItem.Name) : Extension $extensionName is in place and provisioned. Current state: $($extensionTest.ProvisioningState)" -ForegroundColor Green
                    $Wait = $false
                }
            }

            if ($Wait){
            Write-Host "Waiting for extension installation to complete, sleeping for 2 minutes. Attempt $attempts of $maxAttempts"
            Start-Sleep -Seconds 120
            } else {
                break
            }

        } while ($attempts -lt $maxAttempts)

       } #>

}
