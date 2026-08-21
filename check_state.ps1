# ASCII only. Read-only state check for the ComfyUI team deployment.
$t = Get-ScheduledTask -TaskName 'ComfyUI-Team'
'MultipleInstances : ' + $t.Settings.MultipleInstancesPolicy
'ExecutionLimit    : ' + $t.Settings.ExecutionTimeLimit
'LogonType         : ' + $t.Principal.LogonType
'State             : ' + $t.State

$info = Get-ScheduledTaskInfo -TaskName 'ComfyUI-Team'
'LastRunTime       : ' + $info.LastRunTime
'LastTaskResult    : ' + ('0x{0:X8}' -f $info.LastTaskResult)
'NumberOfMissedRuns: ' + $info.NumberOfMissedRuns

$os = Get-CimInstance Win32_OperatingSystem
'LastBootUpTime    : ' + $os.LastBootUpTime
'Now               : ' + (Get-Date)

# Known RAM-fault signature on this host; check whether it recurred.
$bc = Get-WinEvent -FilterHashtable @{LogName='System'; Id=1001; StartTime=(Get-Date).AddDays(-14)} -ErrorAction SilentlyContinue |
      Where-Object { $_.ProviderName -like '*BugCheck*' }
'BugChecks_14d     : ' + ($bc | Measure-Object).Count
$bc | Select-Object -First 5 | ForEach-Object { '  ' + $_.TimeCreated + ' ' + ($_.Message -replace "`r`n", ' ').Substring(0, [Math]::Min(110, $_.Message.Length)) }

$unexp = Get-WinEvent -FilterHashtable @{LogName='System'; Id=41; StartTime=(Get-Date).AddDays(-14)} -ErrorAction SilentlyContinue
'UnexpectedShutdown_14d: ' + ($unexp | Measure-Object).Count
