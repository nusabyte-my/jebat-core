@echo off
REM JEBAT - Start API for Zed Integration

echo ====================================
echo  JEBAT API Server for Zed
echo ====================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not running!
    echo.
    echo Please start Docker Desktop first:
    echo 1. Open Docker Desktop
    echo 2. Wait for it to start
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Auto-create .env from .env.example if missing
if not exist .env (
    if exist .env.example (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env >nul
        echo [OK] .env created. Edit it to set your API keys if needed.
        echo.
    ) else (
        echo [WARNING] No .env or .env.example found. Proceeding with defaults.
        echo.
    )
)

REM Check if JEBAT API is already running
docker ps | findstr jebat-api >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] JEBAT API is already running!
    echo.
    echo API Details:
    echo   URL: http://localhost:8000
    echo   Chat: http://localhost:8000/api/v1/chat/completions
    echo   Key: jebat-local-key
    echo.
    echo Next Steps:
    echo 1. Open Zed editor
    echo 2. Press Ctrl + K (or Cmd + K on Mac)
    echo 3. Select "JEBAT AI" as provider
    echo 4. Start coding with AI!
    echo.
    pause
    exit /b 0
)

echo Starting JEBAT API...
echo.

REM Start JEBAT API
docker-compose up -d jebat-api

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start JEBAT API
    echo.
    echo Troubleshooting:
    echo 1. Make sure you're in the Dev folder
    echo 2. Check if docker-compose.yml exists
    echo 3. Try: docker-compose up -d
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] JEBAT API started successfully!
echo.
echo Waiting for API to be ready...
timeout /t 5 /nobreak >nul

REM Test API
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] API is ready!
) else (
    echo [WARNING] API might still be starting up...
)

echo.
echo ====================================
echo  JEBAT API is Ready for Zed!
echo ====================================
echo.
echo API Details:
echo   Base URL: http://localhost:8000/api/v1
echo   Chat Endpoint: /api/v1/chat/completions
echo   API Key: jebat-local-key
echo.
echo How to Use in Zed:
echo   1. Open any file in Zed
echo   2. Press Ctrl + K (Windows/Linux) or Cmd + K (Mac)
echo   3. Type your question or request
echo   4. Select "JEBAT AI" from provider dropdown
echo   5. Get AI assistance!
echo.
echo Keyboard Shortcuts in Zed:
echo   Ctrl + K           - Open AI chat
echo   Ctrl + Shift + A   - Inline edit
echo   Tab                - Accept completion
echo   Esc                - Dismiss suggestion
echo.
echo Common Use Cases:
echo   - "Explain this code"
echo   - "Add error handling"
echo   - "Write tests for this"
echo   - "Refactor to be cleaner"
echo   - "Find bugs in this code"
echo.
echo Monitoring:
echo   - Analytics: jebat\services\webui\analytics.html
echo   - API Docs: http://localhost:8000/api/docs
echo.
echo To stop API server:
echo   docker-compose stop jebat-api
echo.
pause
