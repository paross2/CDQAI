@echo off
REM CDQAI file version: 2.2.5
setlocal
cd /d "%~dp0"
set /p CDQAI_VERSION=<VERSION
title CDQAI %CDQAI_VERSION% Release Check
echo CDQAI %CDQAI_VERSION% - Release preparation
if not exist ".venv\Scripts\python.exe" (
    echo Python environment missing. Follow INSTALL.txt.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" tools\release_version.py --check
if errorlevel 1 (
    echo Release files are inconsistent. Review tools\release_version.py and GIT_SETUP.md.
    pause
    exit /b 1
)
echo Version check passed for CDQAI %CDQAI_VERSION%.
echo Follow GIT_SETUP.md to test and review the exact files before committing.
echo This helper does not stage, commit, tag, upload files, or process crash data.
pause
