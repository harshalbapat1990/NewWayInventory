@echo off
set LOGFILE=build_log.txt
echo Starting build process... > %LOGFILE%

REM Use the directory of this script as the base path
set BASEDIR=%~dp0

REM Remove trailing backslash if present
if "%BASEDIR:~-1%"=="\" set BASEDIR=%BASEDIR:~0,-1%

set FRONTEND_DIR=%BASEDIR%\frontend
set BACKEND_DIR=%BASEDIR%\backend
set VENV_DIR=%BACKEND_DIR%\venv

REM Step 1: Build the frontend
echo Building the frontend... >> %LOGFILE%
cd "%FRONTEND_DIR%" >> %LOGFILE% 2>&1

REM Clean existing node_modules and package-lock.json to ensure fresh install
echo Cleaning node_modules and package-lock.json... >> %LOGFILE% 2>&1
if exist "%FRONTEND_DIR%\node_modules" (
    echo Removing node_modules folder... >> %LOGFILE% 2>&1
    rmdir /s /q "%FRONTEND_DIR%\node_modules" >> %LOGFILE% 2>&1
)
if exist "%FRONTEND_DIR%\package-lock.json" (
    echo Removing package-lock.json... >> %LOGFILE% 2>&1
    del /f /q "%FRONTEND_DIR%\package-lock.json" >> %LOGFILE% 2>&1
)

REM Install dependencies with legacy-peer-deps flag
echo Installing npm dependencies... >> %LOGFILE% 2>&1
call npm install --legacy-peer-deps >> %LOGFILE% 2>&1
echo NPM install completed with error level: %errorlevel% >> %LOGFILE% 2>&1

REM Build the frontend
echo Running build command... >> %LOGFILE% 2>&1
call npm run build >> %LOGFILE% 2>&1
echo NPM build completed with error level: %errorlevel% >> %LOGFILE% 2>&1

if %errorlevel% neq 0 (
    echo Frontend build failed. Check %LOGFILE% for details. >> %LOGFILE% 2>&1
    echo Frontend build failed. Check %LOGFILE% for details.
    pause
    exit /b %errorlevel%
)

REM Step 2: Copy the dist folder to the backend
echo Copying dist folder to the backend... >> %LOGFILE% 2>&1
if exist "%BACKEND_DIR%\dist" (
    echo Removing existing dist folder in backend... >> %LOGFILE% 2>&1
    rmdir /s /q "%BACKEND_DIR%\dist" >> %LOGFILE% 2>&1
)
echo Copying dist folder from frontend to backend... >> %LOGFILE% 2>&1
xcopy "%FRONTEND_DIR%\dist" "%BACKEND_DIR%\dist" /E /I /Y >> %LOGFILE% 2>&1
echo Copy completed with error level: %errorlevel% >> %LOGFILE% 2>&1

REM Step 3: Navigate to the backend directory
echo Navigating to the backend directory... >> %LOGFILE% 2>&1
cd "%BACKEND_DIR%" >> %LOGFILE% 2>&1

REM Step 4: Activate the virtual environment
echo Activating the virtual environment... >> %LOGFILE% 2>&1
call "%VENV_DIR%\Scripts\activate.bat" >> %LOGFILE% 2>&1
echo Virtual environment activation completed with error level: %errorlevel% >> %LOGFILE% 2>&1

if %errorlevel% neq 0 (
    echo Failed to activate the virtual environment. Check %LOGFILE% for details. >> %LOGFILE% 2>&1
    echo Failed to activate the virtual environment. Check %LOGFILE% for details.
    pause
    exit /b %errorlevel%
)

REM Step 5: Rebuild the executable using PyInstaller
echo Rebuilding the executable with PyInstaller... >> %LOGFILE% 2>&1
call pyinstaller --onefile --add-data "dist;dist" --name InventoryAppBackend run.py >> %LOGFILE% 2>&1
echo PyInstaller completed with error level: %errorlevel% >> %LOGFILE% 2>&1

if %errorlevel% neq 0 (
    echo PyInstaller build failed. Check %LOGFILE% for details. >> %LOGFILE% 2>&1
    echo PyInstaller build failed. Check %LOGFILE% for details.
    pause
    exit /b %errorlevel%
)

REM Step 6: Notify the user
echo Build and packaging complete! The executable is located in the dist folder. >> %LOGFILE% 2>&1
echo Build and packaging complete! The executable is located in the dist folder.
pause