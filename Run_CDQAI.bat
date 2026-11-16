@echo off
REM CDQAI file version: 2.5.1
setlocal
cd /d "%~dp0"
set /p CDQAI_VERSION=<VERSION
powershell -NoProfile -Command "Write-Host '============================================================' -ForegroundColor Blue; Write-Host 'Crash Data Quality Artificial Intelligence (CDQAI)' -ForegroundColor Blue; Write-Host ('Version ' + $env:CDQAI_VERSION) -ForegroundColor Blue; Write-Host ('Installation: ' + $env:CD) -ForegroundColor Blue; Write-Host '============================================================' -ForegroundColor Blue"
echo.
set "CDQAI_PYTHON="
set "CDQAI_PYTHON_ARGS="
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" --version >nul 2>&1
  if not errorlevel 1 set "CDQAI_PYTHON=.venv\Scripts\python.exe"
)
if not defined CDQAI_PYTHON (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3.14 --version >nul 2>&1
    if not errorlevel 1 (
      set "CDQAI_PYTHON=py"
      set "CDQAI_PYTHON_ARGS=-3.14"
    )
  )
)
if not defined CDQAI_PYTHON (
  powershell -NoProfile -Command "Write-Host 'No working Python runtime found. Repair .venv or install Python 3.14.' -ForegroundColor Red"
  pause
  exit /b 1
)
echo Python runtime: %CDQAI_PYTHON% %CDQAI_PYTHON_ARGS%
%CDQAI_PYTHON% %CDQAI_PYTHON_ARGS% tools\ensure_dependencies.py
if errorlevel 1 (
  echo.
  powershell -NoProfile -Command "Write-Host 'A required package could not be installed. Review the error above.' -ForegroundColor Red"
  pause
  exit /b 1
)
%CDQAI_PYTHON% %CDQAI_PYTHON_ARGS% tools\release_version.py --check
if errorlevel 1 (
  powershell -NoProfile -Command "Write-Host 'Release files are inconsistent. See docs\RELEASE_PREFLIGHT.md.' -ForegroundColor Red"
  pause
  exit /b 1
)
for /f %%T in ('powershell -NoProfile -Command "[Diagnostics.Stopwatch]::GetTimestamp()"') do set "CDQAI_START_TICKS=%%T"
%CDQAI_PYTHON% %CDQAI_PYTHON_ARGS% run_cdqai.py --run-all --dated-output
if errorlevel 1 (
  echo.
  powershell -NoProfile -Command "Write-Host ('CDQAI Version ' + $env:CDQAI_VERSION + ' failed. Review the run log in its dated output folder.') -ForegroundColor Red"
  pause
  exit /b 1
)
echo.
for /f %%T in ('powershell -NoProfile -Command "[Diagnostics.Stopwatch]::GetTimestamp()"') do set "CDQAI_END_TICKS=%%T"
powershell -NoProfile -Command "$elapsed = [TimeSpan]::FromSeconds(([double]$env:CDQAI_END_TICKS - [double]$env:CDQAI_START_TICKS) / [Diagnostics.Stopwatch]::Frequency); Write-Host ('Run Successful - Runtime: ' + $elapsed.ToString('d\.hh\:mm\:ss')) -ForegroundColor Green"
echo Dashboard and reports are in the dated output folder shown above.
pause
