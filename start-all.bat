@echo off
echo ========================================================
echo                 STARTING SMRITIX SYSTEM
echo ========================================================
echo.
echo Launching Backend on http://localhost:8000 in background...
start "SMRITIX Backend (FastAPI)" cmd /k "start-backend.bat"

echo Launching Frontend on http://localhost:3000 in background...
start "SMRITIX Frontend (Next.js)" cmd /k "start-frontend.bat"

echo.
echo SMRITIX is booting up!
echo - API Docs: http://localhost:8000/docs
echo - Web App:  http://localhost:3000
echo.
