@echo off
REM CDQAI file version: 2.3.6
setlocal
cd /d "%~dp0"
set /p CDQAI_VERSION=<VERSION
echo ============================================================
echo Crash Data Quality Artificial Intelligence ^(CDQAI^)
echo Version %CDQAI_VERSION%
echo Installation: %CD%
echo ============================================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Python virtual environment not found. Review INSTALL.txt.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" tools\release_version.py --check
if errorlevel 1 (
  echo Release files are inconsistent. See docs\RELEASE_PREFLIGHT.md.
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
