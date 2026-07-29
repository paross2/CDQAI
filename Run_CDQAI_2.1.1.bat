@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo Crash Data Quality Artificial Intelligence ^(CDQAI^)
echo Version 2.1.1 - Build Metadata ^& Provenance
echo ============================================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Python virtual environment not found. Review INSTALL_VERSION_2.1.1.txt.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" run_cdqai.py --run-all
if errorlevel 1 (
  echo.
  echo CDQAI Version 2.1.1 failed. Review the newest log file.
  pause
  exit /b 1
)
echo.
echo CDQAI Version 2.1.1 completed successfully.
echo Dashboard: outputs\dashboard.html
pause
