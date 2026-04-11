@echo off
REM build-cli-bundle.bat
REM Copies required files from jebat-core to packages/cli for npm publishing

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
set "CLI_DIR=%ROOT_DIR%\packages\cli"
set "CORE_DIR=%ROOT_DIR%\jebat-core"

echo.
echo Building CLI bundle...
echo    Root: %ROOT_DIR%
echo    Core: %CORE_DIR%
echo    CLI:  %CLI_DIR%
echo.

REM Verify directories exist
if not exist "%CORE_DIR%" (
    echo Error: jebat-core directory not found at %CORE_DIR%
    exit /b 1
)

if not exist "%CLI_DIR%" (
    echo Error: CLI package directory not found at %CLI_DIR%
    exit /b 1
)

REM Clean existing bundle files in CLI package
echo Cleaning existing bundle files...
cd /d "%CLI_DIR%"

del /f /q AGENTS.md IDENTITY.md MEMORY.md ORCHESTRA.md SOUL.md TOOLS.md USER.md 2>nul
rmdir /s /q adapters vault skills 2>nul

REM Copy identity files
echo Copying identity files...
for %%F in (AGENTS.md IDENTITY.md MEMORY.md ORCHESTRA.md SOUL.md TOOLS.md USER.md) do (
    if exist "%CORE_DIR%\%%F" (
        copy "%CORE_DIR%\%%F" "%CLI_DIR%\%%F" >nul
        echo    [OK] Copied %%F
    ) else (
        echo    [WARN] %%F not found in jebat-core
    )
)

REM Copy adapters directory
echo Copying adapters...
if exist "%CORE_DIR%\adapters" (
    xcopy "%CORE_DIR%\adapters" "%CLI_DIR%\adapters" /E /I /Y >nul
    echo    [OK] Copied adapters/
) else (
    echo    [WARN] adapters directory not found in jebat-core
)

REM Copy vault directory
echo Copying vault...
if exist "%CORE_DIR%\vault" (
    xcopy "%CORE_DIR%\vault" "%CLI_DIR%\vault" /E /I /Y >nul
    echo    [OK] Copied vault/
) else (
    echo    [WARN] vault directory not found in jebat-core
)

REM Copy skills directory
echo Copying skills...
if exist "%CORE_DIR%\skills" (
    xcopy "%CORE_DIR%\skills" "%CLI_DIR%\skills" /E /I /Y >nul
    echo    [OK] Copied skills/
) else (
    echo    [WARN] skills directory not found in jebat-core
)

REM Copy validate-workspace.ps1 if it exists
if exist "%CORE_DIR%\validate-workspace.ps1" (
    copy "%CORE_DIR%\validate-workspace.ps1" "%CLI_DIR%\validate-workspace.ps1" >nul
    echo    [OK] Copied validate-workspace.ps1
)

echo.
echo CLI bundle built successfully!
echo.
echo Ready for npm publish!
echo.

endlocal
