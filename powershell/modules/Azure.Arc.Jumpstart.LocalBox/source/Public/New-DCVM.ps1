function New-DCVM {
    Param (
        $LocalBoxConfig,
        [PSCredential]$localCred,
        [PSCredential]$domainCred
    )
    Write-Host "Creating domain controller VM"
    $adminUser = $env:adminUsername
    $Unattend = GenerateAnswerFile -Hostname $LocalBoxConfig.DCName -IsDCVM $true -LocalBoxConfig $LocalBoxConfig
    Invoke-Command -VMName $LocalBoxConfig.MgmtHostConfig.Hostname -Credential $localCred -ScriptBlock {
        $adminUser = $using:adminUser
        $LocalBoxConfig = $using:LocalBoxConfig
        $localCred = $using:localcred
        $domainCred = $using:domainCred
        $ParentDiskPath = "C:\VMs\Base\"
        $vmpath = "D:\VMs\"
        $OSVHDX = "GUI.vhdx"
        $VMName = $LocalBoxConfig.DCName

        # Create Virtual Machine
        Write-Host "Creating $VMName differencing disks"
        New-VHD -ParentPath ($ParentDiskPath + $OSVHDX) -Path ($vmpath + $VMName + '\' + $VMName + '.vhdx') -Differencing | Out-Null

        Write-Host "Creating $VMName virtual machine"
        New-VM -Name $VMName -VHDPath ($vmpath + $VMName + '\' + $VMName + '.vhdx') -Path ($vmpath + $VMName) -Generation 2 | Out-Null

        Write-Host "Setting $VMName Memory"
        Set-VMMemory -VMName $VMName -DynamicMemoryEnabled $true -StartupBytes $LocalBoxConfig.MEM_DC -MaximumBytes $LocalBoxConfig.MEM_DC -MinimumBytes 500MB | Out-Null

        Write-Host "Configuring $VMName's networking"
        Remove-VMNetworkAdapter -VMName $VMName -Name "Network Adapter" | Out-Null
        Add-VMNetworkAdapter -VMName $VMName -Name $LocalBoxConfig.DCName -SwitchName $LocalBoxConfig.FabricSwitch -DeviceNaming 'On' | Out-Null

        Write-Host "Configuring $VMName's settings"
        Set-VMProcessor -VMName $VMName -Count 2 | Out-Null
        Set-VM -Name $VMName -AutomaticStartAction Start -AutomaticStopAction ShutDown -AutomaticStartDelay 0 | Out-Null

        # Inject Answer File
        Write-Host "Mounting and injecting answer file into the $VMName VM."
        New-Item -Path "C:\TempMount" -ItemType Directory | Out-Null
        Mount-WindowsImage -Path "C:\TempMount" -Index 1 -ImagePath ($vmpath + $VMName + '\' + $VMName + '.vhdx') | Out-Null
        Write-Host "Applying Unattend file to Disk Image..."
        New-Item -Path C:\TempMount\windows -ItemType Directory -Name Panther -Force | Out-Null
        Set-Content -Value $using:Unattend -Path "C:\TempMount\Windows\Panther\Unattend.xml"  -Force
        Write-Host "Dismounting Windows Image"
        Dismount-WindowsImage -Path "C:\TempMount" -Save | Out-Null
        Remove-Item "C:\TempMount" | Out-Null

        # Start Virtual Machine
        Write-Host "Starting Virtual Machine $VMName"
        Start-VM -Name $VMName | Out-Null

        # Wait until the VM is restarted
        while ((Invoke-Command -VMName $VMName -Credential $using:localCred { "Test" } -ea SilentlyContinue) -ne "Test") { Start-Sleep -Seconds 1 }

        Write-Host "Configuring $VMName and Installing Active Directory."
        Invoke-Command -VMName $VMName -Credential $localCred -ArgumentList $LocalBoxConfig -ScriptBlock {
            $LocalBoxConfig = $args[0]
            $DCName = $LocalBoxConfig.DCName
            $IP = $LocalBoxConfig.SDNLABDNS
            $PrefixLength = ($($LocalBoxConfig.MgmtHostConfig.IP).Split("/"))[1]
            $SDNLabRoute = $LocalBoxConfig.SDNLABRoute
            $DomainFQDN = $LocalBoxConfig.SDNDomainFQDN
            $DomainNetBiosName = $DomainFQDN.Split(".")[0]

            Write-Host "Configuring NIC Settings for $DCName"
            $NIC = Get-NetAdapterAdvancedProperty -RegistryKeyWord "HyperVNetworkAdapterName" | Where-Object { $_.RegistryValue -eq $DCName }
            Rename-NetAdapter -name $NIC.name -newname $DCName | Out-Null
            New-NetIPAddress -InterfaceAlias $DCName -IPAddress $ip -PrefixLength $PrefixLength -DefaultGateway $SDNLabRoute | Out-Null
            Set-DnsClientServerAddress -InterfaceAlias $DCName -ServerAddresses $IP | Out-Null
            Install-WindowsFeature -name AD-Domain-Services -IncludeManagementTools | Out-Null

            Write-Host "Configuring Trusted Hosts on $DCName"
            Set-Item WSMan:\localhost\Client\TrustedHosts * -Confirm:$false -Force

            Write-Host "Installing Active Directory forest on $DCName."
            $SecureString = ConvertTo-SecureString $LocalBoxConfig.SDNAdminPassword -AsPlainText -Force
            Install-ADDSForest -DomainName $DomainFQDN -DomainMode 'WinThreshold' -DatabasePath "C:\Domain" -DomainNetBiosName $DomainNetBiosName -SafeModeAdministratorPassword $SecureString -InstallDns -Confirm -Force -NoRebootOnCompletion # | Out-Null
        }

        Write-Host "Stopping $VMName"
        Get-VM $VMName | Stop-VM
        Write-Host "Starting $VMName"
        Get-VM $VMName | Start-VM

        # Wait until DC is created and rebooted
        while ((Invoke-Command -VMName $VMName -Credential $domainCred -ArgumentList $LocalBoxConfig.DCName { (Get-ADDomainController $args[0]).enabled } -ea SilentlyContinue) -ne $true) { Start-Sleep -Seconds 5 }

        Write-Host "Configuring User Accounts and Groups in Active Directory"
        Invoke-Command -VMName $VMName -Credential $domainCred -ArgumentList $LocalBoxConfig, $adminUser -ScriptBlock {
            $LocalBoxConfig = $args[0]
            $adminUser = $args[1]
            $SDNDomainFQDN = $LocalBoxConfig.SDNDomainFQDN
            $SecureString = ConvertTo-SecureString $LocalBoxConfig.SDNAdminPassword -AsPlainText -Force
            Set-ADDefaultDomainPasswordPolicy -ComplexityEnabled $false -Identity $LocalBoxConfig.SDNDomainFQDN -MinPasswordLength 0

            $params = @{
                Name                  = 'NC Admin'
                GivenName             = 'NC'
                Surname               = 'Admin'
                SamAccountName        = 'NCAdmin'
                UserPrincipalName     = "NCAdmin@$SDNDomainFQDN"
                AccountPassword       = $SecureString
                Enabled               = $true
                ChangePasswordAtLogon = $false
                CannotChangePassword  = $true
                PasswordNeverExpires  = $true
            }
            New-ADUser @params

            $params = @{
                Name                  = $adminUser
                GivenName             = 'Jumpstart'
                Surname               = 'Jumpstart'
                SamAccountName        = $adminUser
                UserPrincipalName     = "$adminUser@$SDNDomainFQDN"
                AccountPassword       = $SecureString
                Enabled               = $true
                ChangePasswordAtLogon = $false
                CannotChangePassword  = $true
                PasswordNeverExpires  = $true
            }
            New-ADUser @params

            $params.Name = 'NC Client'
            $params.Surname = 'Client'
            $params.SamAccountName = 'NCClient'
            $params.UserPrincipalName = "NCClient@$SDNDomainFQDN"
            New-ADUser @params

            New-ADGroup -name “NCAdmins” -groupscope Global
            New-ADGroup -name “NCClients” -groupscope Global

            Add-ADGroupMember "Domain Admins" "NCAdmin"
            Add-ADGroupMember "NCAdmins" "NCAdmin"
            Add-ADGroupMember "NCClients" "NCClient"
            Add-ADGroupMember "NCClients" $adminUser
            Add-ADGroupMember "NCAdmins" $adminUser
            Add-ADGroupMember "Domain Admins" $adminUser
            Add-ADGroupMember "NCAdmins" $adminUser
            Add-ADGroupMember "NCClients" $adminUser

            # Set Administrator Account Not to Expire
            Get-ADUser Administrator | Set-ADUser -PasswordNeverExpires $true  -CannotChangePassword $true
            Get-ADUser $adminUser | Set-ADUser -PasswordNeverExpires $true  -CannotChangePassword $true

            # Set DNS Forwarder
            Write-Host "Adding DNS Forwarders"
            Add-DnsServerForwarder $LocalBoxConfig.natDNS

            # Create Enterprise CA
            Write-Host "Installing and Configuring Active Directory Certificate Services and Certificate Templates"
            Install-WindowsFeature -Name AD-Certificate -IncludeAllSubFeature -IncludeManagementTools | Out-Null
            Install-AdcsCertificationAuthority -CAtype 'EnterpriseRootCa' -CryptoProviderName 'ECDSA_P256#Microsoft Software Key Storage Provider' -KeyLength 256 -HashAlgorithmName 'SHA256' -ValidityPeriod 'Years' -ValidityPeriodUnits 10 -Confirm:$false | Out-Null

            # Give WebServer Template Enroll rights for Domain Computers
            $filter = "(CN=WebServer)"
            $ConfigContext = ([ADSI]"LDAP://RootDSE").configurationNamingContext
            $ConfigContext = "CN=Certificate Templates,CN=Public Key Services,CN=Services,$ConfigContext"
            $ds = New-object System.DirectoryServices.DirectorySearcher([ADSI]"LDAP://$ConfigContext", $filter)
            $Template = $ds.Findone().GetDirectoryEntry()

            if ($null -ne $Template) {
                $objUser = New-Object System.Security.Principal.NTAccount("Domain Computers")
                $objectGuid = New-Object Guid 0e10c968-78fb-11d2-90d4-00c04f79dc55
                $ADRight = [System.DirectoryServices.ActiveDirectoryRights]"ExtendedRight"
                $ACEType = [System.Security.AccessControl.AccessControlType]"Allow"
                $ACE = New-Object System.DirectoryServices.ActiveDirectoryAccessRule -ArgumentList $objUser, $ADRight, $ACEType, $objectGuid
                $Template.ObjectSecurity.AddAccessRule($ACE)
                $Template.commitchanges()
            }

            CMD.exe /c "certutil -setreg ca\ValidityPeriodUnits 8" | Out-Null
            Restart-Service CertSvc
            Start-Sleep -Seconds 60

            #Issue Certificate Template
            CMD.exe /c "certutil -SetCATemplates +WebServer"
        }
    }
}
