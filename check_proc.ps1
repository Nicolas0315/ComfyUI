# ASCII only. Why did the ComfyUI process restart? Show its start time and
# any application-level crash events since the last known-good PID.
$conn = Get-NetTCPConnection -LocalPort 8188 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    $p = Get-Process -Id $conn.OwningProcess
    'PID        : ' + $p.Id
    'StartTime  : ' + $p.StartTime
    'CPU_s      : ' + [Math]::Round($p.CPU, 1)
    'WorkingSet : ' + [Math]::Round($p.WorkingSet64 / 1GB, 2) + ' GB'
} else {
    'NOT_LISTENING'
}

'--- Application Error / Hang since 2026-08-10 ---'
Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1002; StartTime=(Get-Date).Date} -ErrorAction SilentlyContinue |
    Select-Object -First 5 |
    ForEach-Object { '  ' + $_.TimeCreated + ' ' + $_.Id + ' ' + ($_.Message -replace "`r`n", ' ').Substring(0, [Math]::Min(120, $_.Message.Length)) }

'--- Task history today ---'
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; StartTime=(Get-Date).Date} -ErrorAction SilentlyContinue |
    Where-Object { $_.Message -like '*ComfyUI-Team*' -and $_.Id -in 102,103,201,203 } |
    Select-Object -First 12 |
    ForEach-Object { '  ' + $_.TimeCreated + ' id=' + $_.Id }
