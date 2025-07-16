::V CMD, zadat daný příkaz: .\dev.bat dev

@echo off
setlocal

REM Check the command line argument passed to the script.
IF /I "%1"=="help" GOTO show_help
IF /I "%1"=="dev-frontend" GOTO dev_frontend
IF /I "%1"=="dev-backend" GOTO dev_backend
IF /I "%1"=="dev" GOTO dev_all
IF "%1"=="" GOTO show_help

REM Handle unknown commands
echo Unknown command: %1
GOTO show_help

:show_help
REM Displays the help message with available commands.
echo Available commands:
echo   dev.bat dev-frontend   - Starts the frontend development server (Vite)
echo   dev.bat dev-backend    - Starts the backend development server (Uvicorn with reload)
echo   dev.bat dev            - Starts both frontend and backend development servers
GOTO :EOF

:dev_frontend
REM Starts the frontend development server in a new window.
echo Starting frontend development server...
start "Frontend" cmd /c "cd frontend && npm run dev"
GOTO :EOF

:dev_backend
REM Starts the backend development server in a new window.
echo Starting backend development server...
start "Backend" cmd /c "cd backend && langgraph dev"
GOTO :EOF

:dev_all
REM Starts both the frontend and backend servers in separate windows.
echo Starting both frontend and backend development servers...
call :dev_frontend
call :dev_backend
GOTO :EOF

:EOF
endlocal