@echo off
setlocal
set "ROOT=%~dp0"
set "FRONTEND=%ROOT%frontend"
set "BACKEND=%ROOT%backend"
if not exist "%FRONTEND%\package-lock.json" (echo package-lock.json is required.& exit /b 1)
where npm >nul 2>&1 || (echo Install Node.js 18+ first.& exit /b 1)
cd /d "%FRONTEND%" || exit /b 1
call npm ci
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
if not exist "%BACKEND%\dist" mkdir "%BACKEND%\dist"
xcopy "%FRONTEND%\dist\*" "%BACKEND%\dist\" /E /I /Y >nul
if errorlevel 1 exit /b 1
if not exist "%BACKEND%\venv\Scripts\python.exe" (echo Create backend\venv and install backend\requirements.txt before packaging.& exit /b 1)
cd /d "%BACKEND%"
call venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --add-data "dist;dist" --name InventoryAppBackend run.py
if errorlevel 1 exit /b 1
echo Build complete. No database or environment secrets were copied into the release.
