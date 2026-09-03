# wa-meta/app/main.py
"""Meta WhatsApp Business API Gateway with enhanced error handling."""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import httpx

app = FastAPI(title="WA Meta Gateway", version="2.0.0")

PORT = int(os.getenv("PORT", 8084))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

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
    phone_id = tenant.get("meta_phone_number_id", "")
    token = tenant.get("meta_token", "")
    
    if not phone_id or not token:
        logger.error(f"Missing credentials for tenant")
        raise HTTPException(status_code=400, detail="Missing Meta API credentials")
    
    version = tenant.get("meta_api_version", "v21.0")
    
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
