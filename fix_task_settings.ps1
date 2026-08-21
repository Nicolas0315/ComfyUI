# ASCII only: PowerShell reads this under CP932 and mangles non-ASCII comments.
# Default ExecutionTimeLimit of 72h kills a resident service (and any in-flight
# generation) every 3 days. Make it unlimited.
$name = 'ComfyUI-Team'

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Set-ScheduledTask -TaskName $name -Settings $settings | Out-Null

$t = Get-ScheduledTask -TaskName $name
'TaskName         : ' + $t.TaskName
'State            : ' + $t.State
'ExecutionLimit   : ' + $t.Settings.ExecutionTimeLimit
'MultipleInstances: ' + $t.Settings.MultipleInstancesPolicy
'LogonType        : ' + $t.Principal.LogonType
'FIX_OK'
