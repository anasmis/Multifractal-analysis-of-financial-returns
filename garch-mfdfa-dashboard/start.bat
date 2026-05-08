@echo off
REM Windows batch script to start the dashboard

echo.
echo 🚀 Starting GARCH + MF-DFA Dashboard...
echo ================================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    echo    Visit: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Compose is not installed. Please install it first.
    echo    Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✓ Docker ^& Docker Compose found
echo.

REM Start services
echo 📦 Building and starting services...
docker-compose up --build

echo.
echo ================================================
echo ✓ Dashboard is ready!
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo ================================================
pause
