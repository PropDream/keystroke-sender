@echo off
REM uninstall.bat — Remove the Chrome Native Messaging host on Windows
setlocal

set HOST_NAME=com.propdream.keystroke_sender
set TARGET_DIR=%LOCALAPPDATA%\Google\Chrome\User Data\NativeMessagingHosts
set SCRIPT_DIR=%~dp0

REM Remove manifest file
if exist "%TARGET_DIR%\%HOST_NAME%.json" (
    del "%TARGET_DIR%\%HOST_NAME%.json"
    echo Removed manifest: %TARGET_DIR%\%HOST_NAME%.json
) else (
    echo Manifest not found — nothing to remove.
)

REM Remove registry key
reg delete "HKCU\Software\Google\Chrome\NativeMessagingHosts\%HOST_NAME%" /f 2>nul
echo Removed registry key.

REM Remove wrapper batch file
if exist "%SCRIPT_DIR%keystroke_sender_wrapper.bat" (
    del "%SCRIPT_DIR%keystroke_sender_wrapper.bat"
    echo Removed wrapper script.
)

echo.
echo Native messaging host '%HOST_NAME%' uninstalled.

endlocal
