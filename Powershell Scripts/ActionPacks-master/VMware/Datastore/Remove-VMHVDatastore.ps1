#Requires -Version 4.0
# Requires -Modules VMware.PowerCLI

<#
.SYNOPSIS
    Removes the specified datastore

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
    https://github.com/scriptrunner/ActionPacks/tree/master/VMware/Datastore

.Parameter VIServer
    Specifies the IP address or the DNS name of the vSphere server to which you want to connect

.Parameter VICredential
    Specifies a PSCredential object that contains credentials for authenticating with the server

.Parameter DatastoreID
    Specifies the ID of the datastore
    
.Parameter DatastoreName
    Specifies the name of the datastore
#>

[CmdLetBinding()]
Param(
    [Parameter(Mandatory = $true,ParameterSetName = "byID")]
    [Parameter(Mandatory = $true,ParameterSetName = "byName")]
    [string]$VIServer,
    [Parameter(Mandatory = $true,ParameterSetName = "byID")]
    [Parameter(Mandatory = $true,ParameterSetName = "byName")]
    [pscredential]$VICredential,
    [Parameter(Mandatory = $true,ParameterSetName = "byName")]
    [string]$DatastoreName,
    [Parameter(Mandatory = $true,ParameterSetName = "byID")]
    [string]$DatastoreID
)

Import-Module VMware.PowerCLI

try{
    $Script:vmServer = Connect-VIServer -Server $VIServer -Credential $VICredential -ErrorAction Stop
    
    if($PSCmdlet.ParameterSetName  -eq "byID"){
        $Script:store = Get-Datastore -Server $Script:vmServer -Refresh:$RefreshFirst -Id $DatastoreID -ErrorAction Stop
    }
    else {
        $Script:store = Get-Datastore -Server $Script:vmServer -Refresh:$RefreshFirst -Name $DatastoreName -ErrorAction Stop
    }
    Remove-Datastore -Datastore $Script:store -Server $Script:vmServer -Confirm:$false -ErrorAction Stop

    if($SRXEnv) {
        $SRXEnv.ResultMessage = "Datastore $($Script:store.Name) removed"
    }
    else{
        Write-Output "Datastore $($Script:store.Name) removed"
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