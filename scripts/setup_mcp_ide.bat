@echo off
REM JEBAT MCP IDE Setup Script (Windows)
REM Automatically configures MCP for your IDE

echo 🗡️ JEBAT MCP IDE Setup
echo ======================
echo.

REM Check if JEBAT is installed
python -c "import jebat" 2>nul
if errorlevel 1 (
    echo ❌ JEBAT not installed. Installing...
    pip install -e .
)

REM Check if MCP is available
python -c "from mcp.server import Server" 2>nul
if errorlevel 1 (
    echo 📦 Installing MCP library...
    pip install mcp
)

REM Detect IDE
echo.
echo Detecting IDE...

set IDE_CONFIG_DIR=
set IDE_NAME=

REM VSCode
if exist "%APPDATA%\Code" (
    set IDE_NAME=VSCode
    set IDE_CONFIG_DIR=%APPDATA%\Code
    echo ✓ Found VSCode
)

REM Zed
if exist "%APPDATA%\dev\zed" (
    set IDE_NAME=Zed
    set IDE_CONFIG_DIR=%APPDATA%\dev\zed
    echo ✓ Found Zed
)

REM Cursor
if exist "%APPDATA%\Cursor" (
    set IDE_NAME=Cursor
    set IDE_CONFIG_DIR=%APPDATA%\Cursor
    echo ✓ Found Cursor
)

if "%IDE_NAME%"=="" (
    echo ⚠️  No supported IDE found. Manual configuration required.
    echo.
    echo See docs\MCP_INTEGRATION_GUIDE.md for manual setup instructions.
    pause
    exit /b 1
)

echo.
echo Configuring MCP for %IDE_NAME%...

REM Create config directory
if not exist "%IDE_CONFIG_DIR%" mkdir "%IDE_CONFIG_DIR%"

REM Copy configuration
if "%IDE_NAME%"=="VSCode" (
    copy /Y "ide-configs\vscode\mcp.json" "%IDE_CONFIG_DIR%\mcp.json"
    copy /Y "ide-configs\vscode\keybindings.json" "%IDE_CONFIG_DIR%\keybindings.json"
    echo ✓ VSCode configuration copied
    echo   Config: %IDE_CONFIG_DIR%\mcp.json
    echo   Keybindings: %IDE_CONFIG_DIR%\keybindings.json
)

if "%IDE_NAME%"=="Zed" (
    copy /Y "ide-configs\zed\settings.json" "%IDE_CONFIG_DIR%\settings.json"
    echo ✓ Zed configuration copied
    echo   Config: %IDE_CONFIG_DIR%\settings.json
)

if "%IDE_NAME%"=="Cursor" (
    if not exist "%IDE_CONFIG_DIR%\.cursor" mkdir "%IDE_CONFIG_DIR%\.cursor"
    copy /Y "ide-configs\cursor\mcp.json" "%IDE_CONFIG_DIR%\.cursor\mcp.json"
    echo ✓ Cursor configuration copied
    echo   Config: %IDE_CONFIG_DIR%\.cursor\mcp.json
)

REM Set environment variable
echo.
echo 📝 Set these environment variables:
echo.
echo   setx JEBAT_API_KEY "your_api_key_here"
echo   setx JEBAT_MODE "assistant"
echo.

REM Test MCP server
echo 🧪 Testing MCP server...
python -m jebat.mcp.server --help >nul 2>&1
if errorlevel 1 (
    echo ⚠️  MCP server test failed. Check installation.
) else (
    echo ✓ MCP server is working!
)

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Set your JEBAT_API_KEY environment variable
echo 2. Restart %IDE_NAME%
echo 3. Open a project and try @jebat in chat
echo.
echo For more info: docs\MCP_INTEGRATION_GUIDE.md
echo.
pause
