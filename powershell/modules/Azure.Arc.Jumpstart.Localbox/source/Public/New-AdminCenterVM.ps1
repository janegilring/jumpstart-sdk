function New-AdminCenterVM {
    Param (
        $LocalBoxConfig,
        $localCred,
        $domainCred
    )
    $VMName = $LocalBoxConfig.WACVMName
    $UnattendXML = GenerateAnswerFile -HostName $VMName -IsWACVM $true -IPAddress $LocalBoxConfig.WACIP -VMMac $LocalBoxConfig.WACMAC -LocalBoxConfig $LocalBoxConfig
    Invoke-Command -VMName AzSMGMT -Credential $localCred -ScriptBlock {
        $VMName = $using:VMName
        $ParentDiskPath = "C:\VMs\Base\"
        $VHDPath = "D:\VMs\"
        $OSVHDX = "GUI.vhdx"
        $BaseVHDPath = $ParentDiskPath + $OSVHDX
        $LocalBoxConfig = $using:LocalBoxConfig
        $localCred = $using:localCred
        $domainCred = $using:domainCred

        # Create Host OS Disk
        Write-Host "Creating $VMName differencing disks"
        New-VHD -ParentPath $BaseVHDPath -Path (($VHDPath) + ($VMName) + '\' + $VMName + (".vhdx")) -Differencing | Out-Null

        # Mount VHDX
        Import-Module DISM
        Write-Host "Mounting $VMName VHD"
        New-Item -Path "C:\TempWACMount" -ItemType Directory | Out-Null
        Mount-WindowsImage -Path "C:\TempWACMount" -Index 1 -ImagePath (($VHDPath) + ($VMName) + '\' + $VMName + (".vhdx")) | Out-Null

        # Copy Source Files
        Write-Host "Copying Application and Script Source Files to $VMName"
        Copy-Item 'C:\Windows Admin Center' -Destination C:\TempWACMount\ -Recurse -Force
        New-Item -Path C:\TempWACMount\VHDs -ItemType Directory -Force | Out-Null
        Copy-Item C:\VMs\Base\AzL-node.vhdx -Destination C:\TempWACMount\VHDs -Force # I dont think this is needed
        Copy-Item C:\VMs\Base\GUI.vhdx  -Destination  C:\TempWACMount\VHDs -Force # I dont think this is needed

        # Create VM
        Write-Host "Provisioning the VM $VMName"
        New-VM -Name $VMName -VHDPath (($VHDPath) + ($VMName) + '\' + $VMName + (".vhdx")) -Path $VHDPath -Generation 2 | Out-Null
        Set-VMMemory -VMName $VMName -DynamicMemoryEnabled $true -StartupBytes $LocalBoxConfig.MEM_WAC -MaximumBytes $LocalBoxConfig.MEM_WAC -MinimumBytes 500MB | Out-Null
        Set-VM -Name $VMName -AutomaticStartAction Start -AutomaticStopAction ShutDown | Out-Null
        Write-Host "Configuring $VMName networking"
        Remove-VMNetworkAdapter -VMName $VMName -Name "Network Adapter"
        Add-VMNetworkAdapter -VMName $VMName -Name "Fabric" -SwitchName $LocalBoxConfig.FabricSwitch -DeviceNaming On
        Set-VMNetworkAdapter -VMName $VMName -StaticMacAddress $LocalBoxConfig.WACMAC # Mac address is linked to the answer file required in next step

        # Apply custom Unattend.xml file
        New-Item -Path C:\TempWACMount\windows -ItemType Directory -Name Panther -Force | Out-Null

        Write-Host "Mounting and Injecting Answer File into the $VMName VM."
        Set-Content -Value $using:UnattendXML -Path "C:\TempWACMount\Windows\Panther\Unattend.xml" -Force
        Write-Host "Dismounting Disk"
        Dismount-WindowsImage -Path "C:\TempWACMount" -Save | Out-Null
        Remove-Item "C:\TempWACMount"

        Write-Host "Setting $VMName's VM Configuration"
        Set-VMProcessor -VMName $VMname -Count 4
        Set-VM -Name $VMName -AutomaticStopAction TurnOff

        Write-Host "Starting $VMName VM."
        Start-VM -Name $VMName

        # Wait until the VM is restarted
        while ((Invoke-Command -VMName $VMName -Credential $domainCred { "Test" } -ea SilentlyContinue) -ne "Test") { Start-Sleep -Seconds 5 }

        # Configure WAC
        Invoke-Command -VMName $VMName -Credential $domainCred -ArgumentList $LocalBoxConfig, $VMName, $domainCred -ScriptBlock {
            $LocalBoxConfig = $args[0]
            $VMName = $args[1]
            $domainCred = $args[2]
            Import-Module NetAdapter

            Write-Host "Enabling Remote Access on $VMName"
            Enable-WindowsOptionalFeature -FeatureName RasRoutingProtocols -All -LimitAccess -Online | Out-Null
            Enable-WindowsOptionalFeature -FeatureName RemoteAccessPowerShell -All -LimitAccess -Online | Out-Null

            Write-Host "Rename Network Adapter in $VMName"
            Get-NetAdapter | Rename-NetAdapter -NewName Fabric

            # Set Gateway
            $index = (Get-WmiObject Win32_NetworkAdapter | Where-Object { $_.netconnectionid -eq "Fabric" }).InterfaceIndex
            $NetInterface = Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object { $_.InterfaceIndex -eq $index }
            $NetInterface.SetGateways($LocalBoxConfig.SDNLABRoute) | Out-Null

            # Enable CredSSP
            Write-Host "Configuring WSMAN Trusted Hosts on $VMName"
            Set-Item WSMan:\localhost\Client\TrustedHosts * -Confirm:$false -Force | Out-Null
            Enable-WSManCredSSP -Role Client -DelegateComputer * -Force | Out-Null
            Enable-PSRemoting -force | Out-Null
            Enable-WSManCredSSP -Role Server -Force | Out-Null
            Enable-WSManCredSSP -Role Client -DelegateComputer localhost -Force | Out-Null
            Enable-WSManCredSSP -Role Client -DelegateComputer $env:COMPUTERNAME -Force | Out-Null
            Enable-WSManCredSSP -Role Client -DelegateComputer $LocalBoxConfig.SDNDomainFQDN -Force | Out-Null
            Enable-WSManCredSSP -Role Client -DelegateComputer "*.$($LocalBoxConfig.SDNDomainFQDN)" -Force | Out-Null
            New-Item -Path HKLM:\SOFTWARE\Policies\Microsoft\Windows\CredentialsDelegation -Name AllowFreshCredentialsWhenNTLMOnly -Force | Out-Null
            New-ItemProperty -Path HKLM:\SOFTWARE\Policies\Microsoft\Windows\CredentialsDelegation\AllowFreshCredentialsWhenNTLMOnly -Name 1 -Value * -PropertyType String -Force | Out-Null

            $WACIP = $LocalBoxConfig.WACIP.Split("/")[0]

            # Install RSAT-NetworkController
            $isAvailable = Get-WindowsFeature | Where-Object { $_.Name -eq 'RSAT-NetworkController' }
            if ($isAvailable) {
                Write-Host "Installing RSAT-NetworkController on $VMName"
                Import-Module ServerManager
                Install-WindowsFeature -Name RSAT-NetworkController -IncludeAllSubFeature -IncludeManagementTools | Out-Null
            }

            # Install Windows features
            Write-Host "Installing Hyper-V RSAT Tools on $VMName"
            Install-WindowsFeature -Name RSAT-Hyper-V-Tools -IncludeAllSubFeature -IncludeManagementTools | Out-Null
            Write-Host "Installing Active Directory RSAT Tools on $VMName"
            Install-WindowsFeature -Name  RSAT-ADDS -IncludeAllSubFeature -IncludeManagementTools | Out-Null
            Write-Host "Installing Failover Clustering RSAT Tools on $VMName"
            Install-WindowsFeature -Name  RSAT-Clustering-Mgmt, RSAT-Clustering-PowerShell -IncludeAllSubFeature -IncludeManagementTools | Out-Null
            Write-Host "Installing DNS Server RSAT Tools on $VMName"
            Install-WindowsFeature -Name RSAT-DNS-Server -IncludeAllSubFeature -IncludeManagementTools | Out-Null
            Install-RemoteAccess -VPNType RoutingOnly | Out-Null

            # Stop Server Manager from starting on boot
            Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\ServerManager" -Name "DoNotOpenServerManagerAtLogon" -Value 1

            # Create BGP Router
            Add-BgpRouter -BGPIdentifier $WACIP -LocalASN $LocalBoxConfig.WACASN -TransitRouting 'Enabled' -ClusterId 1 -RouteReflector 'Enabled'

            $RequestInf = @"
[Version]
Signature="`$Windows NT$"

[NewRequest]
Subject = "CN=$($LocalBoxConfig.WACVMName).$($LocalBoxConfig.SDNDomainFQDN)"
Exportable = True
KeyLength = 2048
KeySpec = 1
KeyUsage = 0xA0
MachineKeySet = True
ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
ProviderType = 12
SMIME = FALSE
RequestType = CMC
FriendlyName = "LocalBox Windows Admin Cert"

[Strings]
szOID_SUBJECT_ALT_NAME2 = "2.5.29.17"
szOID_ENHANCED_KEY_USAGE = "2.5.29.37"
szOID_PKIX_KP_SERVER_AUTH = "1.3.6.1.5.5.7.3.1"
szOID_PKIX_KP_CLIENT_AUTH = "1.3.6.1.5.5.7.3.2"
[Extensions]
%szOID_SUBJECT_ALT_NAME2% = "{text}dns=$($LocalBoxConfig.WACVMName).$($LocalBoxConfig.SDNDomainFQDN)"
%szOID_ENHANCED_KEY_USAGE% = "{text}%szOID_PKIX_KP_SERVER_AUTH%,%szOID_PKIX_KP_CLIENT_AUTH%"
[RequestAttributes]
CertificateTemplate= WebServer
"@

            New-Item C:\WACCert -ItemType Directory -Force | Out-Null
            Set-Content -Value $RequestInf -Path C:\WACCert\WACCert.inf -Force | Out-Null

            Register-PSSessionConfiguration -Name 'Microsoft.SDNNested' -RunAsCredential $domainCred -MaximumReceivedDataSizePerCommandMB 1000 -MaximumReceivedObjectSizeMB 1000
            Write-Host "Requesting and installing SSL Certificate on $using:VMName"
            Invoke-Command -ComputerName $VMName -ConfigurationName 'Microsoft.SDNNested' -Credential $domainCred -ArgumentList $LocalBoxConfig -ScriptBlock {
                $LocalBoxConfig = $args[0]
                # Get the CA Name
                $CertDump = certutil -dump
                $ca = ((((($CertDump.Replace('`', "")).Replace("'", "")).Replace(":", "=")).Replace('\', "")).Replace('"', "") | ConvertFrom-StringData).Name
                $CertAuth = $LocalBoxConfig.SDNDomainFQDN + '\' + $ca

                Write-Host "CA is: $ca"
                Write-Host "Certificate Authority is: $CertAuth"
                Write-Host "Certdump is $CertDump"

                # Request and Accept SSL Certificate
                Set-Location C:\WACCert
                certreq -q -f -new WACCert.inf WACCert.req
                certreq -q -config $CertAuth -attrib "CertificateTemplate:webserver" -submit WACCert.req  WACCert.cer
                certreq -q -accept WACCert.cer
                certutil -q -store my

                Set-Location 'C:\'
                Remove-Item C:\WACCert -Recurse -Force

            } -Authentication Credssp

            # Install Windows Admin Center
            $pfxThumbPrint = (Get-ChildItem -Path Cert:\LocalMachine\my | Where-Object { $_.FriendlyName -match "LocalBox Windows Admin Cert" }).Thumbprint
            Write-Host "Thumbprint: $pfxThumbPrint"
            Write-Host "WACPort: $($LocalBoxConfig.WACport)"
            $WindowsAdminCenterGateway = "https://$($LocalBoxConfig.WACVMName)." + $LocalBoxConfig.SDNDomainFQDN
            Write-Host $WindowsAdminCenterGateway
            Write-Host "Installing and Configuring Windows Admin Center"
            $PathResolve = Resolve-Path -Path 'C:\Windows Admin Center\*.msi'
            $arguments = "/qn /L*v C:\log.txt SME_PORT=$($LocalBoxConfig.WACport) SME_THUMBPRINT=$pfxThumbPrint SSL_CERTIFICATE_OPTION=installed SME_URL=$WindowsAdminCenterGateway"
            Start-Process -FilePath $PathResolve -ArgumentList $arguments -PassThru | Wait-Process

            # Install Chocolatey
            Write-Host "Installing Chocolatey"
            Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            Start-Sleep -Seconds 10

            # Install Azure PowerShell
            Write-Host 'Installing Az PowerShell'
            $expression = "choco install az.powershell -y --limit-output"
            Invoke-Expression $expression

            # Create Shortcut for Hyper-V Manager
            Write-Host "Creating Shortcut for Hyper-V Manager"
            Copy-Item -Path "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Administrative Tools\Hyper-V Manager.lnk" -Destination "C:\Users\Public\Desktop"

            # Create Shortcut for Failover-Cluster Manager
            Write-Host "Creating Shortcut for Failover-Cluster Manager"
            Copy-Item -Path "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Administrative Tools\Failover Cluster Manager.lnk" -Destination "C:\Users\Public\Desktop"

            # Create Shortcut for DNS
            Write-Host "Creating Shortcut for DNS Manager"
            Copy-Item -Path "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Administrative Tools\DNS.lnk" -Destination "C:\Users\Public\Desktop"

            # Create Shortcut for Active Directory Users and Computers
            Write-Host "Creating Shortcut for AD Users and Computers"
            Copy-Item -Path "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Administrative Tools\Active Directory Users and Computers.lnk" -Destination "C:\Users\Public\Desktop"

            # Set Network Profiles
            Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -eq "Public" } | Set-NetConnectionProfile -NetworkCategory Private | Out-Null

            # Disable Automatic Updates
            $WUKey = "HKLM:\software\Policies\Microsoft\Windows\WindowsUpdate"
            New-Item -Path $WUKey -Force | Out-Null
            New-ItemProperty -Path $WUKey -Name AUOptions -PropertyType Dword -Value 2 -Force | Out-Null

            # Install Kubectl
            Write-Host 'Installing kubectl'
            $expression = "choco install kubernetes-cli -y --limit-output"
            Invoke-Expression $expression

            # Create a shortcut for Windows Admin Center
            Write-Host "Creating Shortcut for Windows Admin Center"
            if ($LocalBoxConfig.WACport -ne "443") { $TargetPath = "https://$($LocalBoxConfig.WACVMName)." + $LocalBoxConfig.SDNDomainFQDN + ":" + $LocalBoxConfig.WACport }
            else { $TargetPath = "https://$($LocalBoxConfig.WACVMName)." + $LocalBoxConfig.SDNDomainFQDN }
            $ShortcutFile = "C:\Users\Public\Desktop\Windows Admin Center.url"
            $WScriptShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)
            $Shortcut.TargetPath = $TargetPath
            $Shortcut.Save()

            # Disable Edge 'First Run' Setup
            $edgePolicyRegistryPath  = 'HKLM:SOFTWARE\Policies\Microsoft\Edge'
            $desktopSettingsRegistryPath = 'HKCU:SOFTWARE\Microsoft\Windows\Shell\Bags\1\Desktop'
            $firstRunRegistryName  = 'HideFirstRunExperience'
            $firstRunRegistryValue = '0x00000001'
            $savePasswordRegistryName = 'PasswordManagerEnabled'
            $savePasswordRegistryValue = '0x00000000'
            $autoArrangeRegistryName = 'FFlags'
            $autoArrangeRegistryValue = '1075839525'

            if (-NOT (Test-Path -Path $edgePolicyRegistryPath)) {
                New-Item -Path $edgePolicyRegistryPath -Force | Out-Null
            }
            if (-NOT (Test-Path -Path $desktopSettingsRegistryPath)) {
                New-Item -Path $desktopSettingsRegistryPath -Force | Out-Null
            }

            New-ItemProperty -Path $edgePolicyRegistryPath -Name $firstRunRegistryName -Value $firstRunRegistryValue -PropertyType DWORD -Force
            New-ItemProperty -Path $edgePolicyRegistryPath -Name $savePasswordRegistryName -Value $savePasswordRegistryValue -PropertyType DWORD -Force
            Set-ItemProperty -Path $desktopSettingsRegistryPath -Name $autoArrangeRegistryName -Value $autoArrangeRegistryValue -Force
        }
    }
}
