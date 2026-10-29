:: =============================================================================
:: JEBAT ComfyUI Bridge — LOCAL MACHINE (GPU) launcher
:: =============================================================================
:: Purpose:
::   1. Ensure a Python venv with torch(CUDA) + comfyui on the local workstation
::   2. Start ComfyUI webui (API enabled) on port 8188
::   3. Open an SSH reverse tunnel so the VPS JEBAT MCP can reach the local
::      ComfyUI on the VPS localhost port 8189
::
:: This matches the deployed topology:
::   LOCAL jebat CLI / MCP  --call-->  VPS JEBAT MCP (jebat-mcp, port 8100)
::                                      --calls--> http://127.0.0.1:8189  (tunneled)
::                                      --is-->   Local ComfyUI (port 8188)
::
:: Put this file in the same folder as your JEBAT repo (i.e. next to
:: jebat-mcp.py / this folder). Keep it on the local workstation (GPU box).
:: =============================================================================

@echo off
setlocal

:: --- Config (tweak if you run ComfyUI elsewhere) ---
set "REPO=%~dp0"
set "VENV=%REPO%venv-comfyui"
set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"
set "COMFYUI_DIR=%REPO%ComfyUI"
set "MODELS_DIR=%REPO%models"
set "PORT=8188"
set "TUNNEL_PORT=8189"
set "VPS=72.62.255.206"
set "KEY=%REPO%\.ssh\id_ed25519"

echo.
echo   JEBAT ComfyUI Bridge
echo   Local ComfyUI -> SSH reverse tunnel -> VPS JEBAT MCP
echo.

:: --- 1) Python venv with torch (CUDA) + comfyui -----------------------
if not exist "%PY%" (
    echo [1/4] (venv) Creating Python virtual environment...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo   FAILED to create venv. Install Python 3.9+ and re-run.
        exit /b 1
    )
    echo [1/4] Installing torch (CUDA 12.1) + comfyui...
    call "%PIP%" install --upgrade pip
    call "%PIP%" install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    call "%PIP%" install comfyui
    if errorlevel 1 (
        echo   WARNING: comfyui install may have failed. Check the log below.
    )
    echo   [1/4] venv ready: %PY%
)

:: --- 2) ComfyUI source ------------------------------------------------
if not exist "%COMFYUI_DIR%\main.py" (
    echo [2/4] Cloning ComfyUI...
    git clone https://github.com/comfyui/ComfyUI.git "%COMFYUI_DIR%"
    if errorlevel 1 (
        echo   ComfyUI clone failed. Please clone it manually into %COMFYUI_DIR%
        exit /b 1
    )
)

:: --- 3) start ComfyUI (API enabled) on 8188 ---------------------------
echo [3/4] Starting ComfyUI webui on port %PORT% (API enabled)...
start /b "" "%PY%" "%COMFYUI_DIR%\main.py" --port %PORT% --api --output-dir "%MODELS_DIR%" > "%REPO%comfyui.log" 2>&1
if errorlevel 1 (
    echo   WARNING: ComfyUI may already be running. Check comfyui.log
)
timeout /t 3 /nobreak >nul

:: --- 4) SSH reverse tunnel -> VPS --------------------------------------
echo [4/4] Opening SSH reverse tunnel to VPS %VPS% port %TUNNEL_PORT%...
ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 ^
    -i "%KEY%" -N -f -R "%TUNNEL_PORT%:127.0.0.1:%PORT%" root@"%VPS%"
if errorlevel 1 (
    echo   WARNING: tunnel start returned error (see above). Re-run to retry.
)

echo.
echo   READY. Bridge is now open:
echo     Local ComfyUI   : http://127.0.0.1:%PORT%   (API on 8188)
echo     VPS tunnel port : 127.0.0.1:%TUNNEL_PORT%   (mapped to local 8188)
echo     VPS jebat-mcp   : JEBAT_COMFYUI_HOST=http://127.0.0.1:%TUNNEL_PORT%
echo.
echo   Ask the JEBAT CLI to generate an image and you will get one back.
echo.

:: --- optional cleanup ---------------------------------------------------
:STOP
echo.
echo   Commands:
echo     stop    -> terminates ComfyUI + tunnel (run in same folder)
pause
