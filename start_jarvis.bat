@echo off
echo ===================================================
echo               STARTING JARVIS SYSTEM
echo ===================================================

echo [1/3] Starting Backend (FastAPI)...
start "JARVIS Backend" cmd /k "cd backend && venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting Frontend (React/Vite)...
start "JARVIS Frontend" cmd /k "cd frontend && npm run dev"

echo Waiting 5 seconds for backend and frontend to initialize...
timeout /t 5 /nobreak > NUL

echo [3/3] Starting Desktop App (Electron)...
start "JARVIS Desktop" cmd /c "cd electron && npm start"

echo.
echo JARVIS is now running! 
echo You can close this small window, but keep the other command prompts open while using JARVIS.
timeout /t 5 > NUL
exit
