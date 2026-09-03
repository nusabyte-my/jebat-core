# wa-baileys/Dockerfile
FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache git && \
    npm install --save-exact @whiskeysockets/baileys@6.7.0 express@4.18.2 pino@8.17.2 pino-pretty@10.3.1 qrcode-terminal@0.12.0 dotenv@16.3.1

COPY app/ ./app/

EXPOSE 8085

CMD ["node", "app/index.js"]
