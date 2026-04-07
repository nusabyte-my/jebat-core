"""
Multi-Instance Sync Module — Q3 2027: Distributed System Design

Provides synchronization between multiple JEBAT instances.
Supports distributed memory, federated learning, and edge computing.
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class SyncEventType(str, Enum):
    """Types of sync events."""
    MEMORY_SYNC = "memory.sync"
    CONFIG_SYNC = "config.sync"
    SKILL_SYNC = "skill.sync"
    AUDIT_SYNC = "audit.sync"
    HEARTBEAT = "heartbeat"
    FULL_SYNC = "full.sync"


@dataclass
class SyncEvent:
    """Represents a sync event between instances."""
    event_id: str
    timestamp: str
    event_type: str
    source_instance: str
    target_instance: str
    payload: dict
    checksum: str = ""
    status: str = "pending"  # pending, sent, received, applied, failed
    error: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            payload_json = json.dumps(self.payload, sort_keys=True)
            self.checksum = hashlib.sha256(payload_json.encode()).hexdigest()[:16]


@dataclass
class InstanceInfo:
    """Information about a JEBAT instance."""
    instance_id: str
    name: str
    url: str
    status: str = "unknown"  # online, offline, syncing
    last_heartbeat: str = ""
    version: str = "2.0.0"
    capabilities: list[str] = field(default_factory=list)


class MultiInstanceSync:
    """
    Manages synchronization between multiple JEBAT instances.
    
    Supports:
    - Event-driven sync (webhook-based)
    - Conflict resolution (last-write-wins with checksums)
    - Full sync on demand
    - Health monitoring via heartbeats
    - Capability negotiation
    """
    
    def __init__(self, instance_id: str = None, data_dir: str = None):
        self.instance_id = instance_id or str(uuid.uuid4())[:8]
        self.data_dir = data_dir or os.path.join(os.getcwd(), "security", "sync")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self._instances: dict[str, InstanceInfo] = {}
        self._pending_events: list[SyncEvent] = []
        self._sync_log: list[SyncEvent] = []
    
    def register_instance(self, instance: InstanceInfo):
        """Register a remote instance for syncing."""
        self._instances[instance.instance_id] = instance
    
    def remove_instance(self, instance_id: str):
        """Remove a registered instance."""
        self._instances.pop(instance_id, None)
    
    def emit_event(self, event_type: SyncEventType, payload: dict, target_instance: str = None):
        """Emit a sync event."""
        event = SyncEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.value,
            source_instance=self.instance_id,
            target_instance=target_instance or "broadcast",
            payload=payload,
        )
        self._pending_events.append(event)
        self._sync_log.append(event)
        self._save_sync_log()
    
    def process_event(self, event: SyncEvent) -> bool:
        """Process a received sync event."""
        try:
            # Verify checksum
            payload_json = json.dumps(event.payload, sort_keys=True)
            expected_checksum = hashlib.sha256(payload_json.encode()).hexdigest()[:16]
            if event.checksum != expected_checksum:
                event.status = "failed"
                event.error = "Checksum mismatch"
                return False
            
            # Apply the event (placeholder — actual implementation depends on event type)
            if event.event_type == SyncEventType.MEMORY_SYNC.value:
                self._apply_memory_sync(event.payload)
            elif event.event_type == SyncEventType.CONFIG_SYNC.value:
                self._apply_config_sync(event.payload)
            elif event.event_type == SyncEventType.SKILL_SYNC.value:
                self._apply_skill_sync(event.payload)
            elif event.event_type == SyncEventType.HEARTBEAT.value:
                self._apply_heartbeat(event)
            
            event.status = "applied"
            return True
        except Exception as e:
            event.status = "failed"
            event.error = str(e)
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to all registered instances."""
        self.emit_event(
            SyncEventType.HEARTBEAT,
            {
                "instance_id": self.instance_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "2.0.0",
                "status": "online",
            }
        )
    
    def request_full_sync(self, target_instance: str):
        """Request a full sync from another instance."""
        self.emit_event(
            SyncEventType.FULL_SYNC,
            {
                "requester": self.instance_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            target_instance=target_instance,
        )
    
    def get_pending_events(self) -> list[SyncEvent]:
        """Get events that haven't been sent yet."""
        return [e for e in self._pending_events if e.status == "pending"]
    
    def get_sync_status(self) -> dict:
        """Get synchronization status."""
        return {
            "instance_id": self.instance_id,
            "registered_instances": len(self._instances),
            "pending_events": len([e for e in self._pending_events if e.status == "pending"]),
            "total_events": len(self._sync_log),
            "instances": {
                iid: {"name": i.name, "status": i.status, "last_heartbeat": i.last_heartbeat}
                for iid, i in self._instances.items()
            },
        }
    
    def _apply_memory_sync(self, payload: dict):
        """Apply memory sync event (placeholder)."""
        pass
    
    def _apply_config_sync(self, payload: dict):
        """Apply config sync event (placeholder)."""
        pass
    
    def _apply_skill_sync(self, payload: dict):
        """Apply skill sync event (placeholder)."""
        pass
    
    def _apply_heartbeat(self, event: SyncEvent):
        """Update instance heartbeat."""
        if event.source_instance in self._instances:
            self._instances[event.source_instance].last_heartbeat = event.timestamp
            self._instances[event.source_instance].status = "online"
    
    def _save_sync_log(self):
        """Save sync log to disk."""
        log_file = os.path.join(self.data_dir, "sync-log.json")
        with open(log_file, "w") as f:
            json.dump([e.__dict__ for e in self._sync_log[-1000:]], f, indent=2)


# ─── Federated Learning Design ────────────────────────────────────────────────

class FederatedLearning:
    """
    Federated learning design for distributed JEBAT instances.
    
    Each instance trains local models on its own data,
    then shares model updates (not raw data) with other instances.
    """
    
    def __init__(self):
        self._model_updates: list[dict] = []
    
    def create_local_update(self, model_name: str, weights: dict, metrics: dict) -> dict:
        """Create a local model update."""
        return {
            "model_name": model_name,
            "weights_hash": hashlib.sha256(json.dumps(weights, sort_keys=True).encode()).hexdigest(),
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def aggregate_updates(self, updates: list[dict]) -> dict:
        """Aggregate model updates from multiple instances."""
        # Placeholder: weighted average aggregation
        aggregated = {}
        for update in updates:
            model = update["model_name"]
            if model not in aggregated:
                aggregated[model] = []
            aggregated[model].append(update)
        
        return {
            "aggregated_at": datetime.now(timezone.utc).isoformat(),
            "models": {
                model: {
                    "update_count": len(updates),
                    "metrics": updates[0]["metrics"],
                }
                for model, updates in aggregated.items()
            }
        }
