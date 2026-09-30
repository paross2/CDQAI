@echo off
REM CDQAI file version: 2.3.1
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing. See How To Run.txt.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -B tools\configure_local.py
pause
