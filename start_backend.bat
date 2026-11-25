@echo off
setlocal
where python >nul 2>&1 || (echo Python 3.9+ is required. Install it from python.org, then rerun setup_dev.bat.& exit /b 1)
if not exist "backend\venv\Scripts\python.exe" (echo Development environment is missing. Run setup_dev.bat first.& exit /b 1)
set APP_ENV=development
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
python run.py
