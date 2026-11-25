@echo off
setlocal
set "ROOT=%~dp0"
set "DEST=%~1"
if "%DEST%"=="" (echo Usage: package_app.bat ^<new-empty-destination-folder^>& exit /b 2)
if exist "%DEST%" (echo Destination already exists. Choose a new empty folder.& exit /b 1)
if not exist "%ROOT%backend\dist\InventoryAppBackend.exe" (echo Build the backend executable first.& exit /b 1)
mkdir "%DEST%" || exit /b 1
mkdir "%DEST%\dist" || exit /b 1
copy "%ROOT%backend\dist\InventoryAppBackend.exe" "%DEST%\" >nul || exit /b 1
xcopy "%ROOT%backend\dist\*" "%DEST%\dist\" /E /I /Y >nul
if errorlevel 1 exit /b 1
copy "%ROOT%README.md" "%DEST%\" >nul
copy "%ROOT%SECURITY_DEPLOYMENT.md" "%DEST%\" >nul
echo Release files staged at %DEST%. Database and secrets are intentionally external; configure the HTTPS gateway and persistent data directory separately.

