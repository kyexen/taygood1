@echo off
title Ryt Bank Server
color 0A
cd /d "%~dp0"
echo.
echo ========================================
echo   Ryt Bank - Starting Server...
echo ========================================
echo.
echo Current directory: %CD%
echo.

REM Check Python
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)
python --version
echo.

REM Check dependencies
echo [2/3] Checking dependencies...
python -c "import fastapi, uvicorn, email_validator" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
) else (
    echo Dependencies OK
)
echo.

REM Check .env file
echo [3/4] Checking configuration...
if exist .env (
    echo .env file found
) else (
    echo WARNING: .env file not found
    echo The server will start but AI features won't work without OPENAI_API_KEY
)
echo.

REM Check if port is in use and try to close it
echo [4/4] Checking port 8000...
netstat -ano | findstr :8000 >nul 2>&1
if not errorlevel 1 (
    echo WARNING: Port 8000 is already in use!
    echo Trying to close the process using port 8000...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
        echo Found process with PID: %%a
        taskkill /PID %%a /F >nul 2>&1
        if errorlevel 1 (
            echo Could not close process automatically.
            echo Please close the application using port 8000 manually.
            timeout /t 3 /nobreak >nul
        ) else (
            echo Process closed. Waiting 2 seconds...
            timeout /t 2 /nobreak >nul
        )
    )
) else (
    echo Port 8000 is available
)
echo.

echo.
echo ========================================
echo Starting server on http://localhost:8000
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo Keep this window open while using the app!
echo Open app.html in your browser after server starts
echo.
echo ========================================
echo.

REM Start the server
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

REM If we get here, the server stopped
echo.
echo ========================================
echo Server has stopped
echo ========================================
echo.
pause
