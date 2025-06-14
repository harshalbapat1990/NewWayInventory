@echo off
REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Attempting to install Python...
    REM Download Python installer
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe -OutFile python-installer.exe"
    if exist python-installer.exe (
        REM Install Python silently
        python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
        del python-installer.exe
        echo Python installation completed. Verifying installation...
        
        REM Check if Python is now installed
        python --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo Python installation failed. Please restart your system or install Python manually from https://www.python.org/downloads/
            pause
            exit /b
        )
    ) else (
        echo Failed to download Python installer. Please install Python manually from https://www.python.org/downloads/
        pause
        exit /b
    )
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed. Attempting to install Node.js...
    REM Download Node.js installer
    powershell -Command "Invoke-WebRequest -Uri https://nodejs.org/dist/v16.20.0/node-v16.20.0-x64.msi -OutFile node-installer.msi"
    if exist node-installer.msi (
        REM Install Node.js silently
        msiexec /i node-installer.msi /quiet
        del node-installer.msi
        echo Node.js installation completed. Verifying installation...
        
        REM Check if Node.js is now installed
        node --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo Node.js installation failed. Please restart your system or install Node.js manually from https://nodejs.org/
            pause
            exit /b
        )
    ) else (
        echo Failed to download Node.js installer. Please install Node.js manually from https://nodejs.org/
        pause
        exit /b
    )
)

REM Create the virtual environment inside the backend folder
python -m venv backend\venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b
)

REM Activate the virtual environment
call backend\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b
)

REM Install dependencies
python -m pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b
)

REM Run the backend
python backend\run.py
if %errorlevel% neq 0 (
    echo Failed to run the backend.
    pause
    exit /b
)

pause