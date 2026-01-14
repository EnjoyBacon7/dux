@echo off

:: Set default values for environment variables if not already set
if "%UPLOAD_DIR%"=="" set "UPLOAD_DIR=./uploads"
if "%HOST%"=="" set "HOST=0.0.0.0"
if "%PORT%"=="" set "PORT=8000"
if "%DATABASE_URL%"=="" set "DATABASE_URL=postgresql://dux_user:dux_password@localhost:5433/dux"

:: Display the values of the environment variables
echo UPLOAD_DIR=%UPLOAD_DIR%
echo HOST=%HOST%
echo PORT=%PORT%
echo DATABASE_URL=%DATABASE_URL%

:: Ensure PostgreSQL is installed
where psql >nul 2>&1
if errorlevel 1 (
    echo PostgreSQL is not installed. Please install it first.
    exit /b 1
)

:: Check if PostgreSQL service is running
pg_isready -h localhost -p 5432 >nul 2>&1
if errorlevel 1 (
    echo Starting PostgreSQL service...
    net start postgresql-x64-13 >nul 2>&1
    timeout /t 30 >nul
    pg_isready -h localhost -p 5432 >nul 2>&1
    if errorlevel 1 (
        echo Warning: PostgreSQL failed to start. Database operations may fail.
    ) else (
        echo PostgreSQL is ready!
    )
)

:: Create database and user if they don't exist
psql -U postgres -tc "SELECT 1 FROM pg_user WHERE usename = 'dux_user';" 2>nul | findstr /r /c:"1" >nul
if errorlevel 1 psql -U postgres -c "CREATE USER dux_user WITH PASSWORD 'dux_password';" 2>nul

psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'dux';" 2>nul | findstr /r /c:"1" >nul
if errorlevel 1 psql -U postgres -c "CREATE DATABASE dux OWNER dux_user;" 2>nul

echo Database setup complete!

:: Ensure static directory exists
if not exist static mkdir static

:: Build the frontend and copy to static
echo Building frontend...
cd dux-front
call npm install
call npm run build
cd ..
rd /s /q static >nul 2>&1
mkdir static
xcopy /e /i /y dux-front\dist\* static\ >nul
echo Frontend build complete!

:: Build Docusaurus documentation
echo Building documentation...
cd dux-docs
call npm install
call npm run build
cd ..
:: Copy Docusaurus build to static/docs
if not exist static\docs mkdir static\docs
rd /s /q static\docs >nul 2>&1
mkdir static\docs
xcopy /e /i /y dux-docs\build\* static\docs\ >nul
echo Documentation copied to static/docs

:: Run the application using uvicorn with environment variables
uv run uvicorn server.app:app --reload --host %HOST% --port %PORT% --env-file .env
