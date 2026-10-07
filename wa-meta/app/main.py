# wa-meta/app/main.py
"""Meta WhatsApp Business API Gateway with enhanced error handling.

Note: The Meta app's webhook URL must be configured in Meta dev console
pointing at this service /webhook, verify token = WEBHOOK_VERIFY_TOKEN.
"""
import os
import time
import logging
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import httpx

app = FastAPI(title="WA Meta Gateway", version="2.0.0")

PORT = int(os.getenv("PORT", 8084))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
BOT_URL = os.getenv("BOT_URL", "http://wa-bot:8086")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "")
META_TOKEN = os.getenv("META_TOKEN", os.getenv("META_ACCESS_TOKEN", ""))
META_API_VERSION = os.getenv("META_API_VERSION", "v21.0")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("wa-meta")

class SendRequest(BaseModel):
    to: str
    body: str
    tenant: dict = {}


class TemplateRequest(BaseModel):
    to: str
    template_name: str
    language_code: str = "en_US"
    components: list = []
    tenant: dict = {}


def _url(phone_number_id: str, version: str = "v21.0") -> str:
    return f"https://graph.facebook.com/{version}/{phone_number_id}/messages"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def _post(payload: dict, tenant: dict) -> dict:
    """Send message via Meta Graph API."""
    phone_id = tenant.get("meta_phone_number_id", "") or META_PHONE_NUMBER_ID
    token = tenant.get("meta_token", "") or META_TOKEN
    
    if not phone_id or not token:
        logger.error(f"Missing credentials for tenant")
        raise HTTPException(status_code=400, detail="Missing Meta API credentials")
    
    version = tenant.get("meta_api_version", "") or META_API_VERSION
    try:
        r = httpx.post(
            _url(phone_id, version),
            headers=_headers(token),
            json=payload,
            timeout=30
        )
        
        result = r.json()
        
        if r.status_code != 200:
            error = result.get("error", {})
            logger.warning(f"Meta API {r.status_code}: {error.get('message', 'Unknown error')}")
            # Return structured error for router to decide fallback
            return {
                "success": False,
                "status": r.status_code,
                "error": error.get("message", "Meta API error"),
                "error_code": error.get("code"),
                "error_subcode": error.get("error_subcode"),
                "fallback_eligible": r.status_code in [503, 500, 502, 504]
            }
        
        return {
            "success": True,
            "status": 200,
            "response": result,
            "message_id": result.get("messages", [{}])[0].get("id")
        }
    except httpx.TimeoutException:
        logger.error("Meta API timeout")
        return {
            "success": False,
            "error": "Meta API timeout",
            "fallback_eligible": True
        }
    except Exception as e:
        logger.error(f"Meta API exception: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback_eligible": True
        }

def _process_meta_payload(payload: dict):
    """
    Process incoming Meta WhatsApp webhook payload in background.
    Forwards incoming messages to bot webhook and delivers replies back via Meta Graph API.
    """
    entries = payload.get("entry") or payload.get("entries") or []
    if not isinstance(entries, list):
        return

    for entry in entries:
        changes = entry.get("changes", [])
        if not isinstance(changes, list):
            continue

        for change in changes:
            value = change.get("value", {})
            if not isinstance(value, dict):
                continue

            messages = value.get("messages", [])
            if not messages or not isinstance(messages, list):
                continue

            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id", "") or META_PHONE_NUMBER_ID

            contacts = value.get("contacts", [])
            sender_name = ""
            if contacts and isinstance(contacts, list) and isinstance(contacts[0], dict):
                sender_name = contacts[0].get("profile", {}).get("name", "")

            for msg in messages:
                if not isinstance(msg, dict):
                    continue

                msg_id = msg.get("id", "")
                raw_from = str(msg.get("from", ""))
                from_num = "".join(filter(str.isdigit, raw_from)) or raw_from

                text = ""
                if isinstance(msg.get("text"), dict):
                    text = msg.get("text", {}).get("body", "")
                elif msg.get("type") == "text" and isinstance(msg.get("text"), str):
                    text = msg.get("text", "")
                elif isinstance(msg.get("image"), dict):
                    text = msg.get("image", {}).get("caption", "")

                raw_ts = msg.get("timestamp")
                try:
                    timestamp = int(raw_ts) if raw_ts is not None else int(time.time())
                except (ValueError, TypeError):
                    timestamp = int(time.time())

                contract_payload = {
                    "backend": "meta",
                    "event": "message",
                    "from": from_num,
                    "name": sender_name,
                    "text": text,
                    "message_id": msg_id,
                    "timestamp": timestamp
                }

                logger.info(f"Forwarding Meta message {msg_id} from {from_num} to bot at {BOT_URL}")

                try:
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.post(f"{BOT_URL}/api/v1/webhook", json=contract_payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            replies = data.get("replies", [])
                            if isinstance(replies, list):
                                tenant = {
                                    "meta_phone_number_id": phone_number_id,
                                    "meta_token": META_TOKEN,
                                    "meta_api_version": META_API_VERSION
                                }
                                for reply_text in replies:
                                    if reply_text:
                                        send_payload = {
                                            "messaging_product": "whatsapp",
                                            "recipient_type": "individual",
                                            "to": from_num,
                                            "type": "text",
                                            "text": {"preview_url": False, "body": str(reply_text)}
                                        }
                                        try:
                                            _post(send_payload, tenant)
                                            logger.info(f"Sent reply via Meta to {from_num}")
                                        except Exception as post_err:
                                            logger.error(f"Failed to post Meta reply to {from_num}: {post_err}")
                        else:
                            logger.warning(f"Bot webhook returned non-200 status {resp.status_code}: {resp.text}")
                except Exception as bot_err:
                    logger.error(f"Failed to communicate with bot webhook: {bot_err}")


@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Verify Meta Cloud API webhook challenge.

    Note: The Meta app's webhook URL must be configured in Meta dev console
    pointing at this service /webhook, verify token = WEBHOOK_VERIFY_TOKEN.
    """
    mode = request.query_params.get("hub.mode")
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    expected_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "")

    if mode == "subscribe" and verify_token and verify_token == expected_token:
        logger.info("Meta webhook verified successfully")
        return Response(content=challenge or "", media_type="text/plain")

    logger.warning("Meta webhook verification failed: token mismatch or missing mode")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming Meta WhatsApp Cloud API webhooks.

    Note: The Meta app's webhook URL must be configured in Meta dev console
    pointing at this service /webhook, verify token = WEBHOOK_VERIFY_TOKEN.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.warning(f"Invalid JSON payload on /webhook: {e}")
        return JSONResponse(status_code=200, content={"status": "invalid_json"})

    background_tasks.add_task(_process_meta_payload, payload)
    return JSONResponse(status_code=200, content={"status": "received"})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "wa-meta"}


@app.post("/api/v1/send")
async def send(request: SendRequest):
    """Send text message."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": request.to,
        "type": "text",
        "text": {"preview_url": False, "body": request.body}
    }
    return _post(payload, request.tenant)


@app.post("/api/v1/send-template")
async def send_template(request: TemplateRequest):
    """Send template message."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": request.to,
        "type": "template",
        "template": {
            "name": request.template_name,
            "language": {"code": request.language_code},
            "components": request.components or []
        }
    }
    return _post(payload, request.tenant)


@app.post("/api/v1/send-image")
async def send_image(request: dict):
    """Send image message."""
    to = request.get("to")
    url = request.get("url")
    caption = request.get("caption", "")
    tenant = request.get("tenant", {})
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "image",
        "image": {"link": url}
    }
    if caption:
        payload["image"]["caption"] = caption
    
    return _post(payload, tenant)


@app.post("/api/v1/tenants/{tenant_id}")
async def manage_tenant(tenant_id: str, request: dict):
    """Manage tenant configuration."""
    # Store tenant in memory/database
    return {"success": True, "tenant_id": tenant_id}


@app.get("/openapi.json")
async def openapi():
    return app.openapi()
