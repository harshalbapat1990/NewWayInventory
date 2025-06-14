@echo off
REM Define the source and destination base directories
set SOURCE_DIR=C:\Users\harsh\OneDrive\Work\Inventory app\Inventory app\LatestApp
set DEST_BASE_DIR=C:\Users\harsh\OneDrive\Work\Baba_Work

REM Create a detailed log file
echo Package app script started at %date% %time% > package_log.txt

REM Enable delayed expansion for variable manipulation
setlocal enabledelayedexpansion

REM Find the latest version folder using a simpler approach
set LATEST_NUMBER=0

echo Listing all version folders: >> package_log.txt
for /d %%F in ("%DEST_BASE_DIR%\v1.*") do (
    set "FOLDER_NAME=%%~nxF"
    echo Found folder: !FOLDER_NAME! >> package_log.txt
    
    REM Extract version number using string substitution - remove "v1." prefix
    set "VERSION_STR=!FOLDER_NAME:v1.=!"
    
    REM Remove leading zeros to avoid octal interpretation
    set "VERSION_STR=!VERSION_STR:0=!"
    if "!VERSION_STR!"=="" set "VERSION_STR=0"
    
    REM Convert to number
    set /a VERSION_NUM=!VERSION_STR!
    echo Extracted version: !VERSION_STR! >> package_log.txt
    echo As number: !VERSION_NUM! >> package_log.txt
    
    REM Keep track of highest version number
    if !VERSION_NUM! GTR !LATEST_NUMBER! (
        set LATEST_NUMBER=!VERSION_NUM!
        echo New highest version: !LATEST_NUMBER! >> package_log.txt
    )
)

REM Increment the version number
set /a NEXT_NUMBER=!LATEST_NUMBER! + 1
echo Highest version found: !LATEST_NUMBER!, Next version will be: !NEXT_NUMBER! >> package_log.txt

REM Format the next version string with leading zero for single digit versions
if !NEXT_NUMBER! LSS 10 (
    set NEXT_VERSION=v1.0!NEXT_NUMBER!
) else (
    set NEXT_VERSION=v1.!NEXT_NUMBER!
)
echo Next version folder will be: !NEXT_VERSION! >> package_log.txt

REM Define the destination directory for the new version
set DEST_DIR=%DEST_BASE_DIR%\%NEXT_VERSION%
set INVENTORY_APP_DIR=%DEST_DIR%\InventoryApp

echo Creating directories at: !DEST_DIR! >> package_log.txt

REM Create the new version folder and InventoryApp subfolder
mkdir "%DEST_DIR%" 2>> package_log.txt
mkdir "%INVENTORY_APP_DIR%" 2>> package_log.txt
mkdir "%INVENTORY_APP_DIR%\dist" 2>> package_log.txt

REM Copy the required files and folders into InventoryApp/
echo Copying files to destination... >> package_log.txt
xcopy "%SOURCE_DIR%\backend\dist\InventoryAppBackend.exe" "%INVENTORY_APP_DIR%\" /Y >> package_log.txt 2>&1
xcopy "%SOURCE_DIR%\backend\dist\*" "%INVENTORY_APP_DIR%\dist" /E /Y >> package_log.txt 2>&1
xcopy "%SOURCE_DIR%\backend\instance\inventory.db" "%INVENTORY_APP_DIR%\" /Y >> package_log.txt 2>&1
xcopy "%SOURCE_DIR%\README.txt" "%INVENTORY_APP_DIR%\" /Y >> package_log.txt 2>&1

REM Delete InventoryAppBackend.exe from the dist folder in the destination
del "%INVENTORY_APP_DIR%\dist\InventoryAppBackend.exe" >> package_log.txt 2>&1

REM Create a shortcut to http://192.168.31.230:5000 in the InventoryApp folder
set SHORTCUT_PATH=%INVENTORY_APP_DIR%\Open_App.lnk
set TARGET_URL=http://192.168.31.230:5000
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
set ICON_PATH=%INVENTORY_APP_DIR%\"Icon - logo with name.ico"

REM Copy the icon file to the destination folder
xcopy "%SOURCE_DIR%\Icon - logo with name.ico" "%INVENTORY_APP_DIR%\" /Y >> package_log.txt 2>&1

REM Create shortcut with custom icon
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%CHROME_PATH%'; $s.Arguments = '%TARGET_URL%'; $s.IconLocation = '%ICON_PATH%'; $s.Save()" >> package_log.txt 2>&1

REM Navigate to the version folder
cd "%DEST_DIR%" >> package_log.txt 2>&1

REM Zip the InventoryApp folder within the version folder with the version number in the name
tar -a -c -f "InventoryApp_%NEXT_VERSION%.zip" "InventoryApp" >> package_log.txt 2>&1

REM Notify the user
echo Packaging complete! The new version is located at: %DEST_DIR%
echo The zip file is located at: %DEST_DIR%\InventoryApp_%NEXT_VERSION%.zip
echo Packaging complete %DEST_DIR% >> package_log.txt
echo The zip file is located at: %DEST_DIR%\InventoryApp_%NEXT_VERSION%.zip >> package_log.txt

pause