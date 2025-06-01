
@echo off
title NeonSpark AI Backend Server
echo ============================================
echo NeonSpark AI Backend Server
echo ============================================
echo.

echo Starting backend server on port 3000...
echo Frontend should be running on port 8080
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

:: Change to backend directory
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo ============================================
echo Backend Server Starting...
echo ============================================
echo.
echo Backend URL: http://localhost:3000
echo API Docs: http://localhost:3000/api/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python start_backend.py

echo.
echo Backend server stopped.
pause
