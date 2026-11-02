@echo off
echo Starting SMRITIX FastAPI Backend on http://localhost:8000 ...
cd backend
..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
