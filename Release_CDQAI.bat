@echo off
REM CDQAI file version: 2.5.1
setlocal
cd /d "%~dp0"
set /p CDQAI_VERSION=<VERSION
title CDQAI %CDQAI_VERSION% Release Check
echo CDQAI %CDQAI_VERSION% - Release preparation
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
    echo No working Python runtime found. Repair .venv or install Python 3.14.
    pause
    exit /b 1
)
echo Python runtime: %CDQAI_PYTHON% %CDQAI_PYTHON_ARGS%
%CDQAI_PYTHON% %CDQAI_PYTHON_ARGS% tools\release_version.py --check
if errorlevel 1 (
    echo Release files are inconsistent. Review tools\release_version.py and GIT_SETUP.md.
    pause
    exit /b 1
)
echo Version check passed for CDQAI %CDQAI_VERSION%.
echo Complete docs\RELEASE_PREFLIGHT.md, including the Git inventory check, before pushing main.
echo Each main push triggers source-only verification and a formal GitHub release.
echo This helper does not stage, commit, tag, upload files, or process crash data.
pause
