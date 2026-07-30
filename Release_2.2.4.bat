@echo off
setlocal
title CDQAI Version 2.2.4 Release

cd /d "%~dp0"

echo =============================================
echo   CDQAI Version 2.2.4 Release and Git Commit
echo =============================================
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ERROR: This folder is not a Git repository.
    pause
    exit /b 1
)

echo Running test suite...
python -m pytest -q
if errorlevel 1 (
    echo.
    echo ERROR: Tests failed. Nothing was committed or tagged.
    pause
    exit /b 1
)

echo.
echo Staging Version 2.2.4 files...
git add -A

git diff --cached --quiet
if not errorlevel 1 (
    echo.
    echo No staged changes were found. Nothing to commit.
    pause
    exit /b 0
)

echo.
echo Creating commit...
git commit -m "Release CDQAI v2.2.4: lightweight on-demand narrative evidence"
if errorlevel 1 (
    echo.
    echo ERROR: Git commit failed.
    pause
    exit /b 1
)

git rev-parse "v2.2.4" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo ERROR: Tag v2.2.4 already exists. Commit was created, but no tag or push was performed.
    pause
    exit /b 1
)

echo.
echo Creating annotated tag v2.2.4...
git tag -a v2.2.4 -m "CDQAI Version 2.2.4 - Lightweight On-Demand Narrative Evidence"
if errorlevel 1 (
    echo ERROR: Tag creation failed.
    pause
    exit /b 1
)

echo.
set /p PUSH_RELEASE="Push the commit and tag to origin now? (Y/N): "
if /I "%PUSH_RELEASE%"=="Y" (
    git push origin HEAD
    if errorlevel 1 goto push_failed
    git push origin v2.2.4
    if errorlevel 1 goto push_failed
    echo.
    echo Commit and tag pushed successfully.
) else (
    echo.
    echo Commit and tag were created locally but were not pushed.
)

echo.
git log --oneline -5
pause
exit /b 0

:push_failed
echo.
echo ERROR: Push failed. The local commit and tag still exist.
pause
exit /b 1
