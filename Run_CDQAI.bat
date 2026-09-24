@echo off
REM CDQAI file version: 2.2.5
setlocal
cd /d "%~dp0"
set /p CDQAI_VERSION=<VERSION
echo ============================================================
echo Crash Data Quality Artificial Intelligence ^(CDQAI^)
echo Version %CDQAI_VERSION%
echo ============================================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Python virtual environment not found. Review INSTALL.txt.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" run_cdqai.py --run-all
if errorlevel 1 (
  echo.
  echo CDQAI Version %CDQAI_VERSION% failed. Review the newest log file.
  pause
  exit /b 1
)
echo.
echo CDQAI Version %CDQAI_VERSION% completed successfully.
echo Dashboard: outputs\dashboard.html
pause
