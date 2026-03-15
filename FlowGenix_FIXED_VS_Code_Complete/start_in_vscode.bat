@echo off
echo 🛡️ FlowGenix Ultra-Restrictive System - VS Code Launcher
echo =====================================================

REM Check if VS Code is installed
where code >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ VS Code not found in PATH. Please install VS Code and add it to PATH.
    echo 💡 Download from: https://code.visualstudio.com/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found in PATH. Please install Python.
    echo 💡 Download from: https://python.org/
    pause
    exit /b 1
)

echo ✅ VS Code found
echo ✅ Python found

REM Install dependencies
echo 📦 Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install dependencies. Please check your Python installation.
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Open in VS Code with workspace
echo 🚀 Opening FlowGenix in VS Code...
code FlowGenix.code-workspace

echo 💡 VS Code opened with FlowGenix workspace!
echo 💡 Press F5 in VS Code and select "🚀 FlowGenix UNIFIED (Blocker + UI)"
echo 💡 Or press Ctrl+Shift+P and run "🚀 Start FlowGenix UNIFIED"
echo 💡 This will start BOTH the blocker AND the web UI automatically!

pause
