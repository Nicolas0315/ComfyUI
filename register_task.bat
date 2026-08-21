@echo off
rem ASCII only: cmd.exe mangles non-ASCII bytes under CP932.
rem 5-minute trigger doubles as a watchdog: schtasks defaults to IgnoreNew, so a
rem still-running ComfyUI blocks the next trigger, and a crashed one gets restarted.
setlocal

set TASKNAME=ComfyUI-Team
set TARGET=C:\Users\ogosh\work\ComfyUI\run_comfy_team.bat

schtasks /Delete /TN "%TASKNAME%" /F >nul 2>&1

schtasks /Create /TN "%TASKNAME%" /TR "cmd /c \"%TARGET%\"" /SC MINUTE /MO 5 /RL HIGHEST /F
if errorlevel 1 (
  echo REGISTER_FAILED
  exit /b 1
)

schtasks /Run /TN "%TASKNAME%"
echo REGISTER_OK
