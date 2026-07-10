@echo off
title NeuroMeshOSS Launcher
cls

echo ===================================================
echo   NeuroMeshOSS Production Refinement Launcher      
echo ===================================================
echo.

echo [1/4] Launching Docker local databases and queues...
docker compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Docker Compose failed to launch. Please verify that Docker Desktop is running.
)
echo.

echo Waiting 3 seconds for local databases to initialize...
timeout /t 3 /nobreak >nul
echo.

echo [2/4] Launching FastAPI Control Plane API...
start cmd /k "title NeuroMesh API && echo Starting NeuroMesh API Control Plane... && cd backend && python -m poetry run uvicorn src.main:create_app --factory --host 127.0.0.1 --port 8000 --reload"

echo [3/4] Launching Worker Execution Daemon...
start cmd /k "title NeuroMesh Worker && echo Starting NeuroMesh Worker Daemon... && cd backend && python -m poetry run python src/workers/daemon.py"

echo [4/4] Launching Next.js Console Dashboard...
start cmd /k "title NeuroMesh Dashboard && echo Starting NeuroMesh Next.js Dashboard UI... && cd frontend && npm run dev"

echo.
echo ===================================================
echo   NeuroMeshOSS Services Started Successfully!      
echo ===================================================
echo   - Next.js Dashboard: http://localhost:3000       
echo   - Backend Swagger API: http://localhost:8000/docs
echo ===================================================
echo.
echo Leave this window open or press any key to close the launcher.
pause >nul
