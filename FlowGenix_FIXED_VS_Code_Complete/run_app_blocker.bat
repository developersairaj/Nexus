@echo off
echo 🛡️ Starting FlowGenix App Blocker with Admin Privileges...
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running with Administrator privileges
) else (
    echo ⚠️  Not running as Administrator
    echo Some app blocking features may not work properly
    echo.
    echo Right-click this file and select "Run as administrator" for best results
    timeout /t 3 >nul
)

echo.
echo 🚀 Launching FlowGenix App Blocker...
python app_blocker.py

if %errorLevel% neq 0 (
    echo.
    echo ❌ Error running the app blocker
    echo Make sure Python and required packages are installed
    pause
)

echo.
echo 👋 FlowGenix App Blocker closed
pause
