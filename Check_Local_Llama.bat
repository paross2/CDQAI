@echo off
REM CDQAI file version: 2.3.6
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" -B tools\check_synthetic_ollama.py
pause
