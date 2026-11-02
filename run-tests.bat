@echo off
echo ========================================================
echo               SMRITIX TEST SUITE RUNNER
echo ========================================================
echo.

echo [1/2] Running Backend Pytest Suite...
cd backend
..\backend\.venv\Scripts\python.exe -m pytest -v
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Backend tests failed!
    cd ..
    exit /b %ERRORLEVEL%
)
cd ..

echo.
echo [2/2] Running Frontend Unit Tests...
cd frontend
call npm test
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Frontend tests failed!
    cd ..
    exit /b %ERRORLEVEL%
)
cd ..

echo.
echo ========================================================
echo        ALL SMRITIX TESTS PASSED WITH 100%% SUCCESS!
echo ========================================================
