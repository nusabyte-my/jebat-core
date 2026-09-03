REM === WA Baileys Laptop Startup ===
REM Run this after installing Node.js and npm dependencies

cd /d C:\Users\shaid\Desktop\jebatcore\wa-laptop-tunnel

REM Step 1: Install deps (first time only)
call npm install --save-exact @whiskeysockets/baileys@6.7.0 express@4.18.2 pino@8.17.2 qrcode-terminal@0.12.0

REM Step 2: Start Baileys (scan QR in terminal)
echo "Starting Baileys - scan QR in terminal..."
node baileys-server.js

REM Step 3: In a new terminal, start ngrok
REM ngrok http 8085 --region=ap

REM Step 4: Copy ngrok URL to VPS
REM docker exec wa-router env BAILEYS_URL=http://xxxx.ngrok.io/api/v1/send
