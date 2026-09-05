@echo off
TITLE Specter AI Code Review Engine - Engineered by Divyansh Mishra
COLOR 0B

echo =====================================================================
echo   SPECTER AI CODE REVIEW ENGINE
echo   Principal Autonomous Multi-Turn Code Reviewer
echo   Engineered by Divyansh Mishra - All Rights Reserved
echo =====================================================================
echo.

REM Verify Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

REM Verify Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found in PATH. Please install Node.js 18+.
    pause
    exit /b 1
)

echo [1/3] Starting Specter Backend Server on http://localhost:8000...
start "Specter Backend API (FastAPI)" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Waiting for backend initialization...
timeout /t 3 /nobreak >nul

echo [3/3] Starting Specter Frontend Dashboard on http://localhost:5173...
start "Specter Frontend (Vite React)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo =====================================================================
echo   Specter AI is launching!
echo   Dashboard: http://localhost:5173
echo   API Docs:  http://localhost:8000/docs
echo =====================================================================
echo.
timeout /t 2 /nobreak >nul
start http://localhost:5173
pause
