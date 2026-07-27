@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo Crash Data Quality Artificial Intelligence ^(CDQAI^)
echo Version 2.0.2 - Annual Reporting Reliability
echo ============================================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: .venv\Scripts\python.exe was not found.
  echo Create or restore the project virtual environment first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" run_cdqai.py --run-all
if errorlevel 1 (
  echo.
  echo CDQAI Version 2.0.2 failed. Review the newest log file.
  pause
  exit /b 1
)
echo.
echo CDQAI Version 2.0.2 completed successfully.
echo Dashboard: outputs\dashboard.html
pause
