@echo off
REM === WA Baileys SSH Reverse Tunnel ===
REM Makes VPS:8085 forward to laptop:8085
REM Run this AFTER starting baileys-server.js

echo Starting SSH reverse tunnel...
echo VPS 72.62.255.206:8085 -> laptop:8085
echo.

:loop
ssh -R 8085:localhost:8085 -N -o "ServerAliveInterval=30" -o "ServerAliveCountMax=3" -o "ExitOnForwardFailure=yes" root@72.62.255.206
echo Tunnel dropped. Reconnecting in 5s...
timeout /t 5
goto loop
