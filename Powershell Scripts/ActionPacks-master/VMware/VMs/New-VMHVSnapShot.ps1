#Requires -Version 4.0
# Requires -Modules VMware.PowerCLI

<#
.SYNOPSIS
    Creates a new snapshot of a virtual machine

.DESCRIPTION

.NOTES
    This PowerShell script was developed and optimized for ScriptRunner. The use of the scripts requires ScriptRunner. 
    The customer or user is authorized to copy the script from the repository and use them in ScriptRunner. 
    The terms of use for ScriptRunner do not apply to this script. In particular, ScriptRunner Software GmbH assumes no liability for the function, 
    the use and the consequences of the use of this freely available script.
    PowerShell is a product of Microsoft Corporation. ScriptRunner is a product of ScriptRunner Software GmbH.
    © ScriptRunner Software GmbH

.COMPONENT
    Requires Module VMware.PowerCLI

.LINK
    https://github.com/scriptrunner/ActionPacks/tree/master/VMware/VMs

.Parameter VIServer
    Specifies the IP address or the DNS name of the vSphere server to which you want to connect

.Parameter VICredential
    Specifies a PSCredential object that contains credentials for authenticating with the server

.Parameter VMId
    Specifies the ID of the virtual machine you want to snapshot

.Parameter VMName
    Specifies the name of the virtual machine you want to snapshot

.Parameter Name
    Specifies a name for the new snapshot

.Parameter Description
    Provide a description of the new snapshot

.Parameter Memory
    If the virtual machine is powered on, the virtual machine's memory state is preserved with the snapshot

.Parameter Quiesce
    VMware Tools are used to quiesce the file system of the virtual machine. 
    This assures that a disk snapshot represents a consistent state of the guest file systems
#>

[CmdLetBinding()]
Param(
    [Parameter(Mandatory = $true,ParameterSetName = "byID")]
    [Parameter(Mandatory = $true,ParameterSetName = "byName")]
    [string]$VIServer,
    [Parameter(Mandatory = $true,ParameterSetName = "byID")]
    [Parameter(Mandatory = $true,ParameterSetName = "byName")]
    [pscredential]$VICredential,
    [Parameter(Mandatory = $true,ParameterSetName = "byID")]
    [string]$VMId,
    [Parameter(Mandatory = $true,ParameterSetName = "byName")]
    [string]$VMName,
    [Parameter(Mandatory = $true,ParameterSetName = "byID")]
    [Parameter(Mandatory = $true,ParameterSetName = "byName")]
    [string]$Name, 
    [Parameter(ParameterSetName = "byID")]
    [Parameter(ParameterSetName = "byName")]
    [string]$Description,
    [Parameter(ParameterSetName = "byID")]
    [Parameter(ParameterSetName = "byName")]
    [switch]$Memory,
    [Parameter(ParameterSetName = "byID")]
    [Parameter(ParameterSetName = "byName")]
    [switch]$Quiesce
)

Import-Module VMware.PowerCLI

try{
    [string[]]$Properties = @('Name','Created','PowerState','SizeGB','Description','IsCurrent','Id')
    if([System.String]::IsNullOrWhiteSpace($Description) -eq $true){
        $Description = " "
    }
    $Script:vmServer = Connect-VIServer -Server $VIServer -Credential $VICredential -ErrorAction Stop

    if($PSCmdlet.ParameterSetName  -eq "byID"){
        $Script:machine = Get-VM -Server $Script:vmServer -Id $VMId -ErrorAction Stop
    }
    else{
        $Script:machine = Get-VM -Server $Script:vmServer -Name $VMName -ErrorAction Stop
    }
    $result = New-Snapshot -Server $Script:vmServer -VM $Script:machine -Name $Name `
                        -Description $Description -Memory:$Memory -Quiesce:$Quiesce `
                        -Confirm:$false -ErrorAction Stop | Select-Object $Properties

    if($SRXEnv) {
        $SRXEnv.ResultMessage = $result
    }
    else{
        Write-Output $result
    }
}
catch{
    throw
}
finally{    
    if($null -ne $Script:vmServer){
        Disconnect-VIServer -Server $Script:vmServer -Force -Confirm:$false
    }
}