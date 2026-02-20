@echo off
REM install.bat — Install the Chrome Native Messaging host on Windows
setlocal enabledelayedexpansion

set HOST_NAME=com.propdream.keystroke_sender
set SCRIPT_DIR=%~dp0
set HOST_PATH=%SCRIPT_DIR%keystroke_sender_wrapper.bat

REM Create the wrapper batch file that Chrome will execute
echo @echo off > "%SCRIPT_DIR%keystroke_sender_wrapper.bat"
echo python -m keystroke_sender.host %%* >> "%SCRIPT_DIR%keystroke_sender_wrapper.bat"

REM Set manifest directory
set TARGET_DIR=%LOCALAPPDATA%\Google\Chrome\User Data\NativeMessagingHosts

REM Prompt for Chrome extension ID
set /p EXTENSION_ID="Enter your Chrome extension ID (found at chrome://extensions): "

if "%EXTENSION_ID%"=="" (
    echo Error: Extension ID cannot be empty.
    exit /b 1
)

REM Create target directory
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

REM Write the native messaging host manifest
(
echo {
echo   "name": "%HOST_NAME%",
echo   "description": "Simulates OS-level keystrokes for Chrome Form Filler",
echo   "path": "%HOST_PATH:\=\\%",
echo   "type": "stdio",
echo   "allowed_origins": [
echo     "chrome-extension://%EXTENSION_ID%/"
echo   ]
echo }
) > "%TARGET_DIR%\%HOST_NAME%.json"

REM Add registry key (required on Windows)
reg add "HKCU\Software\Google\Chrome\NativeMessagingHosts\%HOST_NAME%" /ve /t REG_SZ /d "%TARGET_DIR%\%HOST_NAME%.json" /f

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r "%SCRIPT_DIR%requirements.txt"

echo.
echo Native messaging host '%HOST_NAME%' installed successfully.
echo   Manifest: %TARGET_DIR%\%HOST_NAME%.json
echo   Host:     %HOST_PATH%
echo   Registry: HKCU\Software\Google\Chrome\NativeMessagingHosts\%HOST_NAME%

endlocal
