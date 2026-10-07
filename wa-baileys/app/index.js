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
const BOT_URL = process.env.BOT_URL || 'http://wa-bot:8086';

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

    sock.ev.on('messages.upsert', async (m) => {
        try {
            const messages = m.messages || [];
            for (const msg of messages) {
                if (!msg || !msg.message) continue;
                if (msg.key?.fromMe) continue;

                const remoteJid = msg.key?.remoteJid || '';
                if (!remoteJid || remoteJid.includes('@g.us')) continue;

                const rawFrom = remoteJid.split('@')[0];
                const from = rawFrom.split(':')[0].replace(/\D/g, '') || rawFrom.split(':')[0];
                if (!from) continue;

                const text = msg.message.conversation || msg.message.extendedTextMessage?.text || msg.message.imageMessage?.caption || '';
                const name = msg.pushName || '';
                const message_id = msg.key?.id || '';
                const timestamp = Number(msg.messageTimestamp) || Math.floor(Date.now() / 1000);

                const payload = {
                    backend: 'baileys',
                    event: 'message',
                    from,
                    name,
                    text,
                    message_id,
                    timestamp
                };

                try {
                    const botRes = await fetch(`${BOT_URL}/api/v1/webhook`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                        signal: AbortSignal.timeout(10000)
                    });

                    if (!botRes.ok) {
                        logger.warn(`Bot webhook responded with status ${botRes.status}`);
                        continue;
                    }

                    const data = await botRes.json();
                    const replies = Array.isArray(data?.replies) ? data.replies : [];
                    for (const entry of replies) {
                        if (entry && sock) {
                            await sock.sendMessage(`${from}@s.whatsapp.net`, { text: entry });
                            logger.info(`Sent reply to ${from} via Baileys`);
                        }
                    }
                } catch (botErr) {
                    logger.error(`Error communicating with bot webhook: ${botErr.message}`);
                }
            }
        } catch (err) {
            logger.error(`Error in messages.upsert handler: ${err.message}`);
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

// Bot status proxy
app.get('/api/v1/bot/status', async (req, res) => {
    try {
        const response = await fetch(`${BOT_URL}/health`, { signal: AbortSignal.timeout(5000) });
        if (response.ok) {
            const data = await response.json().catch(() => ({}));
            return res.json({ bot: 'online', ...data });
        } else {
            return res.json({ bot: 'offline', status: response.status });
        }
    } catch (err) {
        logger.warn(`Bot health proxy failed: ${err.message}`);
        return res.json({ bot: 'offline', error: err.message });
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

// Send document
app.post('/api/v1/send-document', async (req, res) => {
    try {
        const { to, documentBase64, url, fileName, caption, tenant } = req.body || {};

        if (!to || (!documentBase64 && !url) || !fileName) {
            return res.json({
                success: false,
                error: 'Missing required fields (to, fileName, documentBase64 or url)'
            });
        }

        if (!isConnected) {
            return res.json({
                success: false,
                error: 'WhatsApp not connected',
                fallback_eligible: false
            });
        }

        const jid = to.includes('@s.whatsapp.net') ? to : `${to}@s.whatsapp.net`;

        const payload = documentBase64
            ? { document: Buffer.from(documentBase64, 'base64'), fileName, caption: caption || '' }
            : { document: { url }, fileName, caption: caption || '' };

        const result = await sock.sendMessage(jid, payload);

        res.json({
            success: true,
            message_id: result?.key?.id,
            backend: 'baileys'
        });
    } catch (error) {
        logger.error(`Send document error: ${error.message}`);
        res.json({
            success: false,
            error: error.message,
            fallback_eligible: true
        });
    }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    logger.info(`Baileys gateway running on port ${PORT}`);
    startSock();
});
