"""
LLM-to-LLM Agent Communication Protocol
Standardized protocol for cross-provider agent communication.

Enables:
- OpenAI agents ↔ Anthropic agents ↔ Gemini agents ↔ Ollama agents
- Request/Response, Broadcast, Subscribe/Publish, Delegation
- Conversation state management across providers
- Message translation between provider formats
"""

import json
import uuid
import asyncio
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ─── Protocol Message Types ────────────────────────────────────────────────────

class MessageType(str, Enum):
    """Types of messages agents can exchange."""
    # Direct communication
    REQUEST = "request"                    # Ask another agent to do something
    RESPONSE = "response"                  # Reply to a request
    REJECTION = "rejection"                # Decline a request
    
    # Broadcast
    BROADCAST = "broadcast"                # Send to all agents
    ANNOUNCEMENT = "announcement"          # Broadcast without expecting response
    
    # Delegation
    DELEGATE = "delegate"                  # Pass task to another agent
    SUB_DELEGATE = "sub_delegate"          # Agent delegates to sub-agent
    RETURN_DELEGATION = "return_delegation" # Return results to delegator
    
    # Collaboration
    PROPOSAL = "proposal"                  # Propose a solution/approach
    COUNTER_PROPOSAL = "counter_proposal"  # Counter another agent's proposal
    VOTE = "vote"                          # Vote on a proposal
    CONSENSUS = "consensus"                # Consensus reached
    
    # Status
    STATUS_UPDATE = "status_update"        # Agent status change
    PROGRESS = "progress"                  # Task progress update
    ERROR = "error"                        # Error notification
    TIMEOUT = "timeout"                    # Request timed out
    
    # Lifecycle
    REGISTER = "register"                  # Agent registers with system
    DEREGISTER = "deregister"              # Agent leaves system
    HEARTBEAT = "heartbeat"                # Agent alive check


class Priority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentStatus(str, Enum):
    """Agent availability status."""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    THINKING = "thinking"
    WAITING = "waiting"  # Waiting for another agent


@dataclass
class AgentIdentity:
    """Unique identity of an LLM agent."""
    agent_id: str                          # Unique ID (e.g., "tukang-001")
    agent_name: str                        # Display name (e.g., "Tukang")
    agent_role: str                        # Role (e.g., "development")
    provider: str                          # LLM provider (openai, anthropic, gemini, ollama, zai)
    model: str                             # Specific model (gpt-4o, claude-sonnet-4, etc.)
    capabilities: list[str]                # What this agent can do
    languages: list[str] = field(default_factory=lambda: ["en"])
    max_context_tokens: int = 128000
    status: AgentStatus = AgentStatus.IDLE
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentMessage:
    """Standardized message format for cross-provider communication."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""              # Groups related messages
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Sender/Recipient
    sender: AgentIdentity = None
    recipient: str = ""                    # Agent ID, "broadcast", or "any"
    
    # Content
    message_type: MessageType = MessageType.REQUEST
    priority: Priority = Priority.MEDIUM
    subject: str = ""                      # Brief summary
    content: str = ""                      # Main message content
    structured_data: dict = field(default_factory=dict)  # Additional data
    
    # Control
    requires_response: bool = True
    timeout_seconds: float = 30.0
    expires_at: str = ""
    parent_message_id: str = ""            # For threaded conversations
    reply_to_message_id: str = ""          # Direct reply reference
    
    # Routing
    route_path: list[str] = field(default_factory=list)  # Message path history
    max_hops: int = 10                     # Prevent infinite loops
    current_hop: int = 0
    
    def __post_init__(self):
        if not self.expires_at and self.timeout_seconds > 0:
            from datetime import timedelta
            expires = datetime.now(timezone.utc) + timedelta(seconds=self.timeout_seconds)
            self.expires_at = expires.isoformat()
    
    def to_json(self) -> str:
        data = asdict(self)
        # Serialize nested objects
        if self.sender:
            data['sender'] = self.sender.to_dict()
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        data = json.loads(json_str)
        if data.get('sender'):
            data['sender'] = AgentIdentity(**data['sender'])
        # Convert enums
        data['message_type'] = MessageType(data['message_type'])
        data['priority'] = Priority(data['priority'])
        if 'status' in data.get('sender', {}):
            pass  # Already handled above
        return cls(**data)
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > datetime.fromisoformat(self.expires_at)


@dataclass
class ConversationState:
    """Tracks the state of a multi-agent conversation."""
    conversation_id: str
    title: str
    initiator: str                        # Agent ID who started it
    participants: list[str]                # All participating agent IDs
    messages: list[AgentMessage] = field(default_factory=list)
    status: str = "active"                # active, paused, completed, failed
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = ""
    result: str = ""
    metadata: dict = field(default_factory=dict)
    
    def add_message(self, message: AgentMessage):
        self.messages.append(message)
        if message.message_type == MessageType.RESPONSE and message.reply_to_message_id:
            # Find parent and mark as resolved
            for msg in self.messages:
                if msg.message_id == message.reply_to_message_id:
                    msg.structured_data['resolved'] = True
                    break
    
    def get_message_thread(self, message_id: str) -> list[AgentMessage]:
        """Get all messages in a thread."""
        thread = []
        for msg in self.messages:
            if msg.message_id == message_id or msg.parent_message_id == message_id or msg.reply_to_message_id == message_id:
                thread.append(msg)
        return sorted(thread, key=lambda m: m.timestamp)
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['messages'] = [
            json.loads(m.to_json()) if isinstance(m, AgentMessage) else m 
            for m in self.messages
        ]
        return data


# ─── Message Templates ────────────────────────────────────────────────────────

class MessageTemplates:
    """Pre-built message templates for common agent interactions."""
    
    @staticmethod
    def request_help(requester: AgentIdentity, helper: str, task: str, context: str = "") -> AgentMessage:
        return AgentMessage(
            sender=requester,
            recipient=helper,
            message_type=MessageType.REQUEST,
            subject=f"Help needed: {task[:50]}",
            content=f"""Agent {requester.agent_name} ({requester.provider}/{requester.model}) needs assistance.

Task: {task}

Context:
{context}

Please review and respond with your analysis or solution.""",
            priority=Priority.HIGH,
            requires_response=True,
            timeout_seconds=60.0,
        )
    
    @staticmethod
    def delegate_task(delegator: AgentIdentity, delegatee: str, task: str, constraints: dict = None) -> AgentMessage:
        return AgentMessage(
            sender=delegator,
            recipient=delegatee,
            message_type=MessageType.DELEGATE,
            subject=f"Delegated task: {task[:50]}",
            content=f"""Delegation from {delegator.agent_name} ({delegator.provider}/{delegator.model})

Task: {task}

Constraints:
{json.dumps(constraints or {}, indent=2)}

Please execute this task and return results via return_delegation message.""",
            priority=Priority.HIGH,
            requires_response=True,
            timeout_seconds=120.0,
        )
    
    @staticmethod
    def propose_solution(proposer: AgentIdentity, recipients: list[str], proposal: str, alternatives: list[str] = None) -> AgentMessage:
        alternatives_text = "\n\nAlternatives considered:\n" + "\n".join(f"- {a}" for a in (alternatives or [])) if alternatives else ""
        return AgentMessage(
            sender=proposer,
            recipient=recipients[0] if len(recipients) == 1 else "broadcast",
            message_type=MessageType.PROPOSAL,
            subject=f"Proposal: {proposal[:50]}",
            content=f"""Proposal from {proposer.agent_name} ({proposer.provider}/{proposer.model})

{proposal}
{alternatives_text}

Please review and vote: AGREE, DISAGREE, or ABSTAIN with reasoning.""",
            priority=Priority.MEDIUM,
            requires_response=True,
            timeout_seconds=45.0,
        )
    
    @staticmethod
    def broadcast_announcement(sender: AgentIdentity, message: str) -> AgentMessage:
        return AgentMessage(
            sender=sender,
            recipient="broadcast",
            message_type=MessageType.ANNOUNCEMENT,
            subject=message[:50],
            content=f"""Announcement from {sender.agent_name} ({sender.provider}/{sender.model})

{message}

No response required.""",
            priority=Priority.LOW,
            requires_response=False,
        )
    
    @staticmethod
    def error_notification(sender: AgentIdentity, recipient: str, error: str, context: str = "") -> AgentMessage:
        return AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.ERROR,
            subject=f"Error: {error[:50]}",
            content=f"""Error notification from {sender.agent_name} ({sender.provider}/{sender.model})

Error: {error}

Context:
{context}

Please advise on resolution.""",
            priority=Priority.CRITICAL,
            requires_response=True,
            timeout_seconds=30.0,
        )


# ─── Protocol Serializer ──────────────────────────────────────────────────────

class ProtocolSerializer:
    """Converts messages to/from provider-specific formats."""
    
    @staticmethod
    def to_openai_format(message: AgentMessage) -> list[dict]:
        """Convert AgentMessage to OpenAI chat format."""
        return [
            {"role": "system", "content": f"You are {message.sender.agent_name}, a {message.sender.agent_role} agent running on {message.sender.provider} ({message.sender.model})."},
            {"role": "user", "content": message.content},
        ]
    
    @staticmethod
    def to_anthropic_format(message: AgentMessage) -> dict:
        """Convert AgentMessage to Anthropic messages format."""
        return {
            "system": f"You are {message.sender.agent_name}, a {message.sender.agent_role} agent running on {message.sender.provider} ({message.sender.model}).",
            "messages": [
                {"role": "user", "content": message.content},
            ]
        }
    
    @staticmethod
    def from_provider_response(provider: str, response: Any, original_message: AgentMessage) -> AgentMessage:
        """Convert provider response back to AgentMessage."""
        content = ""
        if provider == "openai":
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        elif provider == "anthropic":
            content = response.get("content", [{}])[0].get("text", "") if isinstance(response.get("content"), list) else response.get("content", "")
        elif provider == "gemini":
            content = response.get("text", "")
        elif provider == "ollama":
            content = response.get("message", {}).get("content", response.get("response", ""))
        elif provider == "zai":
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return AgentMessage(
            sender=original_message.sender,  # Will be replaced by actual responder
            recipient=original_message.sender.agent_id if original_message.sender else "",
            message_type=MessageType.RESPONSE,
            subject=f"Response to: {original_message.subject}",
            content=content,
            parent_message_id=original_message.message_id,
            reply_to_message_id=original_message.message_id,
            conversation_id=original_message.conversation_id,
            requires_response=False,
        )
