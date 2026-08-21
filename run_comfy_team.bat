@echo off
rem ASCII only: cmd.exe reads this as CP932 and mangles non-ASCII comment bytes.
rem Log is truncated on every start, which doubles as the retention rule.
rem Manager stays OFF: arbitrary custom-node install from an exposed surface is RCE.
cd /d "%~dp0"

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

rem 127.0.0.1 for cloudflared, 100.93.250.118 (Tailscale) for admin access
".venv\Scripts\python.exe" main.py ^
  --listen 127.0.0.1,100.93.250.118 ^
  --port 8188 ^
  --highvram --use-pytorch-cross-attention --reserve-vram 1.5 ^
  --preview-method none ^
  > comfy_team.log 2>&1
