@echo off
setlocal
where python >nul 2>&1 || (echo Install Python 3.9+ first.& exit /b 1)
where node >nul 2>&1 || (echo Install Node.js 18+ first.& exit /b 1)
python -m venv --upgrade backend\venv || exit /b 1
call backend\venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r backend\requirements-dev.txt
if errorlevel 1 exit /b 1
cd /d "%~dp0frontend"
npm ci
if errorlevel 1 exit /b 1
echo Setup complete. Set APP_ENV=development and run start_backend.bat; run npm run dev in frontend.

