"""
Audit Logging Module — Q2 2027: Compliance and Audit Trail

Provides structured audit logging for all JEBAT operations.
Supports GDPR, SOC2, and ISO 27001 compliance requirements.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AuditEventType(str, Enum):
    """Types of audit events."""
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    MEMORY_DELETE = "memory.delete"
    AGENT_EXECUTE = "agent.execute"
    AGENT_SPAWN = "agent.spawn"
    SCAN_RUN = "security.scan"
    SCAN_FIX = "security.fix"
    CONFIG_CHANGE = "config.change"
    USER_CREATE = "user.create"
    USER_DELETE = "user.delete"
    ROLE_ASSIGN = "role.assign"
    DATA_EXPORT = "data.export"
    API_CALL = "api.call"
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"


class ComplianceFramework(str, Enum):
    """Compliance frameworks supported."""
    GDPR = "gdpr"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


@dataclass
class AuditEvent:
    """Represents a single audit event."""
    event_id: str
    timestamp: str
    event_type: str
    actor_id: str
    actor_role: str
    target_resource: str
    action: str
    result: str  # success, failure, denied
    source_ip: str = ""
    user_agent: str = ""
    details: dict = None
    compliance_frameworks: list = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.compliance_frameworks is None:
            self.compliance_frameworks = []
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Structured audit logger for JEBAT.
    
    Writes to:
    - JSON file (for local development)
    - Elasticsearch (for production)
    - stdout (for debugging)
    """
    
    def __init__(self, log_dir: str = None, elasticsearch_url: str = None):
        self.log_dir = log_dir or os.path.join(os.getcwd(), "security", "audit-logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        self._file_logger = logging.getLogger("jebat.audit")
        self._file_logger.setLevel(logging.INFO)
        
        # File handler
        log_file = os.path.join(self.log_dir, f"audit-{datetime.now().strftime('%Y%m%d')}.log")
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter("%(message)s"))
        self._file_logger.addHandler(fh)
        
        # Elasticsearch client (optional)
        self._es_client = None
        if elasticsearch_url:
            try:
                from elasticsearch import Elasticsearch
                self._es_client = Elasticsearch(elasticsearch_url)
            except ImportError:
                pass
    
    def log(self, event_type: AuditEventType, actor_id: str, actor_role: str,
            target_resource: str, action: str, result: str,
            source_ip: str = "", user_agent: str = "", details: dict = None,
            compliance_frameworks: list = None) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.value,
            actor_id=actor_id,
            actor_role=actor_role,
            target_resource=target_resource,
            action=action,
            result=result,
            source_ip=source_ip,
            user_agent=user_agent,
            details=details or {},
            compliance_frameworks=compliance_frameworks or [],
        )
        
        # Write to file
        self._file_logger.info(event.to_json())
        
        # Write to Elasticsearch
        if self._es_client:
            self._es_client.index(index="jebat-audit", document=event.to_dict())
        
        return event
    
    def get_events(self, start_date: str = None, end_date: str = None,
                   event_type: str = None, actor_id: str = None,
                   limit: int = 100) -> list[AuditEvent]:
        """Query audit events."""
        events = []
        log_file = os.path.join(self.log_dir, f"audit-{datetime.now().strftime('%Y%m%d')}.log")
        
        if not os.path.exists(log_file):
            return []
        
        with open(log_file) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    event = AuditEvent(**data)
                    
                    # Apply filters
                    if start_date and event.timestamp < start_date:
                        continue
                    if end_date and event.timestamp > end_date:
                        continue
                    if event_type and event.event_type != event_type:
                        continue
                    if actor_id and event.actor_id != actor_id:
                        continue
                    
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return events
    
    def generate_compliance_report(self, framework: ComplianceFramework,
                                    start_date: str, end_date: str) -> dict:
        """Generate a compliance report for a specific framework."""
        events = self.get_events(start_date=start_date, end_date=end_date)
        
        report = {
            "framework": framework.value,
            "period": {"start": start_date, "end": end_date},
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_events": len(events),
            "event_summary": {},
            "actor_summary": {},
            "result_summary": {},
            "compliance_checks": self._get_compliance_checks(framework, events),
        }
        
        # Summarize events
        for event in events:
            report["event_summary"][event.event_type] = report["event_summary"].get(event.event_type, 0) + 1
            report["actor_summary"][event.actor_id] = report["actor_summary"].get(event.actor_id, 0) + 1
            report["result_summary"][event.result] = report["result_summary"].get(event.result, 0) + 1
        
        return report
    
    def _get_compliance_checks(self, framework: ComplianceFramework, events: list) -> dict:
        """Get compliance-specific checks."""
        checks = {}
        
        if framework == ComplianceFramework.GDPR:
            checks = {
                "data_access_logged": any(e.event_type in ("memory.read", "memory.write", "data.export") for e in events),
                "auth_events_logged": any(e.event_type.startswith("auth.") for e in events),
                "user_consent_tracked": any(e.event_type == "config.change" for e in events),
            }
        elif framework == ComplianceFramework.SOC2:
            checks = {
                "access_controls_logged": any(e.event_type.startswith("auth.") for e in events),
                "system_changes_logged": any(e.event_type == "config.change" for e in events),
                "security_events_logged": any(e.event_type.startswith("security.") for e in events),
            }
        elif framework == ComplianceFramework.ISO27001:
            checks = {
                "incident_response_logged": any(e.event_type.startswith("security.") for e in events),
                "access_management_logged": any(e.event_type.startswith("auth.") for e in events),
                "change_management_logged": any(e.event_type == "config.change" for e in events),
            }
        
        return checks


# ─── FastAPI Middleware ────────────────────────────────────────────────────────

def create_audit_middleware(audit_logger: AuditLogger):
    """Create FastAPI middleware for automatic audit logging."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    
    class AuditMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Log API calls
            if request.url.path.startswith("/api/"):
                response = await call_next(request)
                
                audit_logger.log(
                    event_type=AuditEventType.API_CALL,
                    actor_id="anonymous",
                    actor_role="user",
                    target_resource=request.url.path,
                    action=f"{request.method} {request.url.path}",
                    result="success" if response.status_code < 400 else "failure",
                    source_ip=request.client.host if request.client else "",
                    user_agent=request.headers.get("user-agent", ""),
                )
                
                return response
            
            return await call_next(request)
    
    return AuditMiddleware
