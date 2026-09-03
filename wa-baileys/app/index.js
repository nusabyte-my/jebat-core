// wa-baileys/app/index.js
const express = require('express');
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const pino = require('pino');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8085;
const SESSION_DIR = process.env.SESSION_DIR || '/app/sessions';
const LOG_LEVEL = process.env.LOG_LEVEL || 'info';

const logger = pino({ level: LOG_LEVEL });

const app = express();
app.use(express.json());

let sock = null;
let isConnected = false;
let qrCode = null;

// Ensure session directory exists
if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
}

async function startSock() {
    const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
    
    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        logger: pino({ level: 'silent' }),
        browser: ['WA Gateway', 'Chrome', '1.0.0']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            qrCode = qr;
            logger.info('QR Code generated - scan to connect');
            console.log('\n\n=== SCAN THIS QR CODE ===');
            qrcode.generate(qr, { small: true });
            console.log('========================\n');
        }

        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            logger.warn(`Connection closed. Error: ${lastDisconnect?.error?.message}. Reconnect: ${shouldReconnect}`);
            isConnected = false;
            if (shouldReconnect) {
                setTimeout(startSock, 5000);
            }
        } else if (connection === 'open') {
            isConnected = true;
            qrCode = null;
            logger.info('WhatsApp connected');
        }
    });

    sock.ev.on('messages.upsert', (m) => {
        // Handle incoming messages if needed
        const msg = m.messages[0];
        if (!msg.key.fromMe && m.type === 'notify') {
            logger.info(`Received message from ${msg.key.remoteJid}`);
        }
    });
}

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: isConnected ? 'ok' : 'waiting',
        service: 'wa-baileys',
        connected: isConnected,
        has_qr: !!qrCode
    });
});

// Get QR code
app.get('/api/v1/qr', (req, res) => {
    if (qrCode) {
        res.json({ qr: qrCode, message: 'Scan this QR code with WhatsApp' });
    } else if (isConnected) {
        res.json({ message: 'Already connected', connected: true });
    } else {
        res.json({ message: 'QR not ready yet. Waiting for generation...', connected: false });
    }
});

// Send text message
app.post('/api/v1/send', async (req, res) => {
    try {
        const { to, body, tenant } = req.body;
        
        if (!isConnected) {
            return res.json({
                success: false,
                error: 'WhatsApp not connected',
                fallback_eligible: false
            });
        }

        if (!to || !body) {
            return res.json({
                success: false,
                error: 'Missing to or body'
            });
        }

        // Format phone number
        const jid = to.includes('@s.whatsapp.net') ? to : `${to}@s.whatsapp.net`;
        
        const result = await sock.sendMessage(jid, { text: body });
        
        res.json({
            success: true,
            message_id: result?.key?.id,
            backend: 'baileys'
        });
    } catch (error) {
        logger.error(`Send error: ${error.message}`);
        res.json({
            success: false,
            error: error.message,
            fallback_eligible: true
        });
    }
});

// Send image
app.post('/api/v1/send-image', async (req, res) => {
    try {
        const { to, url, caption, tenant } = req.body;
        
        if (!isConnected) {
            return res.json({
                success: false,
                error: 'WhatsApp not connected'
            });
        }

        const jid = to.includes('@s.whatsapp.net') ? to : `${to}@s.whatsapp.net`;
        
        const result = await sock.sendMessage(jid, {
            image: { url: url },
            caption: caption || ''
        });
        
        res.json({
            success: true,
            message_id: result?.key?.id,
            backend: 'baileys'
        });
    } catch (error) {
        logger.error(`Send image error: ${error.message}`);
        res.json({
            success: false,
            error: error.message
        });
    }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    logger.info(`Baileys gateway running on port ${PORT}`);
    startSock();
});
