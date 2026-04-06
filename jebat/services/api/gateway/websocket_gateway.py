"""
JEBAT WebSocket Gateway with MCP Support

Enhanced WebSocket gateway that integrates MCP protocol, multi-channel communication,
decision engine, error recovery, and smart caching for real-time AI assistant interactions.

Key Features:
- MCP Protocol Server Integration
- Multi-Channel WebSocket Support
- Intelligent Message Routing via Decision Engine
- Automatic Error Recovery
- Session Management
- Real-time Presence and Events
- Hot/Cold Message Queues
- Authentication & Authorization
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import aiohttp
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""

    # Client to Server
    MESSAGE = "message"
    AUTH = "auth"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"

    # Server to Client
    RESPONSE = "response"
    ERROR = "error"
    EVENT = "event"
    PRESENCE = "presence"
    PONG = "pong"
    NOTIFICATION = "notification"


class ConnectionState(Enum):
    """WebSocket connection states"""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ChannelType(Enum):
    """Supported communication channels"""

    WEBSOCKET = "websocket"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    SIGNAL = "signal"
    IMESSAGE = "imessage"
    MATRIX = "matrix"
    EMAIL = "email"
    VOICE = "voice"


@dataclass
class WebSocketSession:
    """WebSocket session with full context"""

    session_id: str
    websocket: WebSocketServerProtocol
    state: ConnectionState = ConnectionState.CONNECTING
    user_id: Optional[str] = None
    channel: ChannelType = ChannelType.WEBSOCKET
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)

    def is_active(self, timeout_minutes: int = 30) -> bool:
        """Check if session is still active"""
        return self.state in [
            ConnectionState.CONNECTED,
            ConnectionState.AUTHENTICATED,
        ] and (datetime.utcnow() - self.last_activity) < timedelta(
            minutes=timeout_minutes
        )

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "user_id": self.user_id,
            "channel": self.channel.value,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "subscriptions": list(self.subscriptions),
            "capabilities": self.capabilities,
        }


@dataclass
class WebSocketMessage:
    """Standard WebSocket message format"""

    type: MessageType
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type.value,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "reply_to": self.reply_to,
            "payload": self.payload,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebSocketMessage":
        """Create from dictionary"""
        return cls(
            type=MessageType(data["type"]),
            payload=data.get("payload", {}),
            message_id=data.get("message_id"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            reply_to=data.get("reply_to"),
            metadata=data.get("metadata", {}),
        )


class WebSocketGateway:
    """
    Enhanced WebSocket Gateway with MCP Integration

    Provides real-time bidirectional communication between AI clients and JEBAT:
    - WebSocket connection management
    - Message routing and handling
    - Session management
    - Multi-channel support
    - MCP protocol integration
    - Decision engine integration
    - Error recovery
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 18789,
        max_connections: int = 100,
        session_timeout: int = 30,
        enable_mcp: bool = True,
        mcp_port: int = 18790,
    ):
        """
        Initialize WebSocket Gateway

        Args:
            host: Host to bind to
            port: Port to listen on
            max_connections: Maximum concurrent connections
            session_timeout: Session timeout in minutes
            enable_mcp: Enable MCP protocol server
            mcp_port: Port for MCP protocol server
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.session_timeout = session_timeout
        self.enable_mcp = enable_mcp
        self.mcp_port = mcp_port

        # Session management
        self.sessions: Dict[str, WebSocketSession] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(
            set
        )  # user_id -> session_ids
        self._sessions_lock = asyncio.Lock()

        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.MESSAGE: self._handle_message,
            MessageType.AUTH: self._handle_auth,
            MessageType.SUBSCRIBE: self._handle_subscribe,
            MessageType.UNSUBSCRIBE: self._handle_unsubscribe,
            MessageType.PING: self._handle_ping,
        }

        # Channel handlers
        self.channel_handlers: Dict[ChannelType, Callable] = {}

        # Event subscribers
        self.event_subscribers: Dict[str, Set[str]] = defaultdict(
            set
        )  # event -> session_ids

        # External integrations
        self.mcp_server = None
        self.decision_engine = None
        self.error_recovery = None
        self.cache_client = None
        self.memory_system = None

        # Message queues
        self.hot_queue: deque = deque(maxlen=1000)  # High priority, low latency
        self.cold_queue: deque = deque(maxlen=10000)  # Standard priority

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._queue_processor_task: Optional[asyncio.Task] = None
        self._mcp_server_task: Optional[asyncio.Task] = None
        self._is_running = False

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_sessions": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "auth_failures": 0,
        }

        logger.info(f"WebSocket Gateway initialized on {host}:{port}")
        logger.info(f"MCP Support: {'enabled' if enable_mcp else 'disabled'}")

    def register_mcp_server(self, mcp_server):
        """Register MCP protocol server"""
        self.mcp_server = mcp_server
        logger.info("MCP Server registered with WebSocket Gateway")

    def register_decision_engine(self, decision_engine):
        """Register decision engine for intelligent routing"""
        self.decision_engine = decision_engine
        logger.info("Decision Engine registered with WebSocket Gateway")

    def register_error_recovery(self, error_recovery):
        """Register error recovery system"""
        self.error_recovery = error_recovery
        logger.info("Error Recovery System registered with WebSocket Gateway")

    def register_cache_client(self, cache_client):
        """Register cache client"""
        self.cache_client = cache_client
        logger.info("Cache Client registered with WebSocket Gateway")

    def register_memory_system(self, memory_system):
        """Register memory system"""
        self.memory_system = memory_system
        logger.info("Memory System registered with WebSocket Gateway")

    def register_channel_handler(self, channel: ChannelType, handler: Callable):
        """Register handler for specific channel type"""
        self.channel_handlers[channel] = handler
        logger.info(f"Channel handler registered: {channel.value}")

    async def start(self):
        """Start WebSocket gateway and MCP server"""
        if self._is_running:
            logger.warning("WebSocket Gateway is already running")
            return

        self._is_running = True

        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        self._queue_processor_task = asyncio.create_task(self._process_message_queues())

        # Start MCP server if enabled
        if self.enable_mcp and self.mcp_server:
            self._mcp_server_task = asyncio.create_task(self.mcp_server.start())

        logger.info("WebSocket Gateway started successfully")

    async def stop(self):
        """Stop WebSocket gateway and all background tasks"""
        if not self._is_running:
            return

        self._is_running = False

        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._queue_processor_task:
            self._queue_processor_task.cancel()
        if self._mcp_server_task:
            self._mcp_server_task.cancel()

        # Close all sessions
        async with self._sessions_lock:
            for session in list(self.sessions.values()):
                try:
                    await session.websocket.close()
                except Exception as e:
                    logger.error(f"Error closing session {session.session_id}: {e}")

        self.sessions.clear()
        self.user_sessions.clear()

        logger.info("WebSocket Gateway stopped")

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """
        Handle new WebSocket connection

        Args:
            websocket: WebSocket connection
            path: Request path
        """
        session_id = str(uuid.uuid4())

        # Check connection limit
        if len(self.sessions) >= self.max_connections:
            logger.warning(f"Connection limit reached, rejecting: {session_id}")
            await websocket.close(code=1008, reason="Server at capacity")
            return

        # Create session
        session = WebSocketSession(
            session_id=session_id, websocket=websocket, state=ConnectionState.CONNECTED
        )

        # Add to sessions
        async with self._sessions_lock:
            self.sessions[session_id] = session
            self.stats["total_connections"] += 1
            self.stats["active_sessions"] = len(self.sessions)

        logger.info(
            f"New WebSocket connection: {session_id} from {websocket.remote_address}"
        )

        try:
            # Send welcome message
            welcome_msg = WebSocketMessage(
                type=MessageType.EVENT,
                payload={
                    "event": "connected",
                    "session_id": session_id,
                    "server_time": datetime.utcnow().isoformat(),
                },
            )
            await self._send_to_session(session, welcome_msg)

            # Start message handling loop
            await self._handle_session_messages(session)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {session_id}")
        except Exception as e:
            logger.error(f"Error handling session {session_id}: {e}")
            self.stats["errors"] += 1
        finally:
            await self._cleanup_session(session_id)

    async def _handle_session_messages(self, session: WebSocketSession):
        """
        Handle incoming messages from a session

        Args:
            session: WebSocket session
        """
        async for message in session.websocket:
            try:
                session.update_activity()
                self.stats["messages_received"] += 1

                # Parse message
                data = json.loads(message)
                ws_message = WebSocketMessage.from_dict(data)

                # Route to handler
                handler = self.message_handlers.get(ws_message.type)
                if handler:
                    await handler(session, ws_message)
                else:
                    # Unknown message type
                    error_msg = WebSocketMessage(
                        type=MessageType.ERROR,
                        payload={
                            "error": "Unknown message type",
                            "type": ws_message.type.value,
                        },
                        reply_to=ws_message.message_id,
                    )
                    await self._send_to_session(session, error_msg)
                    self.stats["errors"] += 1

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON message from {session.session_id}: {e}")
                self.stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error handling message from {session.session_id}: {e}")
                self.stats["errors"] += 1

    async def _handle_message(
        self, session: WebSocketSession, message: WebSocketMessage
    ):
        """
        Handle incoming user message

        Args:
            session: WebSocket session
            message: WebSocket message
        """
        try:
            # Check authentication
            if session.state != ConnectionState.AUTHENTICATED:
                raise PermissionError("Authentication required")

            # Use decision engine for routing
            if self.decision_engine:
                from decision_engine.engine import DecisionContext, DecisionType

                # Create decision context
                context = DecisionContext(
                    user_id=session.user_id,
                    request=message.payload.get("content", ""),
                    request_type="message",
                    task_data=message.payload,
                    user_history=await self._get_user_history(session.user_id),
                    memory_context=await self._get_memory_context(session.user_id),
                    current_session=session.to_dict(),
                )

                # Make routing decision
                decisions = await self.decision_engine.decide(context)

                # Process based on decision
                await self._process_message_with_decision(session, message, decisions)
            else:
                # Fallback: simple processing
                await self._process_message_simple(session, message)

        except Exception as e:
            logger.error(f"Error handling message: {e}")

            # Use error recovery if available
            if self.error_recovery:
                try:
                    await self.error_recovery.handle_error(
                        e,
                        {
                            "component": "gateway",
                            "operation": "handle_message",
                            "session_id": session.session_id,
                            "user_id": session.user_id,
                        },
                    )
                except Exception as recovery_error:
                    logger.error(f"Error recovery failed: {recovery_error}")

            # Send error response
            error_msg = WebSocketMessage(
                type=MessageType.ERROR,
                payload={"error": str(e), "message": "Failed to process message"},
                reply_to=message.message_id,
            )
            await self._send_to_session(session, error_msg)

    async def _process_message_with_decision(
        self, session: WebSocketSession, message: WebSocketMessage, decisions: Dict
    ):
        """
        Process message using decision engine routing

        Args:
            session: WebSocket session
            message: WebSocket message
            decisions: Decisions from decision engine
        """
        # Get routing decision
        agent_decision = decisions.get("agent")
        route_decision = decisions.get("route")
        priority_decision = decisions.get("priority")

        # Add to appropriate queue based on priority
        if priority_decision and priority_decision.selected_option.value == "critical":
            self.hot_queue.append((session, message, decisions))
        else:
            self.cold_queue.append((session, message, decisions))

        # Send acknowledgment
        ack_msg = WebSocketMessage(
            type=MessageType.RESPONSE,
            payload={
                "status": "queued",
                "priority": priority_decision.selected_option.value
                if priority_decision
                else "normal",
                "agent": agent_decision.selected_option if agent_decision else None,
                "estimated_time": route_decision.metadata.get("estimated_time", 0)
                if route_decision
                else None,
            },
            reply_to=message.message_id,
        )
        await self._send_to_session(session, ack_msg)

    async def _process_message_simple(
        self, session: WebSocketSession, message: WebSocketMessage
    ):
        """
        Simple message processing without decision engine

        Args:
            session: WebSocket session
            message: WebSocket message
        """
        # Add to cold queue
        self.cold_queue.append((session, message, {}))

        # Send acknowledgment
        ack_msg = WebSocketMessage(
            type=MessageType.RESPONSE,
            payload={"status": "queued"},
            reply_to=message.message_id,
        )
        await self._send_to_session(session, ack_msg)

    async def _process_message_queues(self):
        """Process messages from hot and cold queues"""
        while self._is_running:
            try:
                # Process hot queue first (higher priority)
                if self.hot_queue:
                    await self._process_queue_item(
                        self.hot_queue.popleft(), priority="high"
                    )
                elif self.cold_queue:
                    await self._process_queue_item(
                        self.cold_queue.popleft(), priority="normal"
                    )
                else:
                    # No messages to process
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing message queue: {e}")
                await asyncio.sleep(1)

    async def _process_queue_item(self, item: Tuple, priority: str):
        """
        Process individual queue item

        Args:
            item: Queue item (session, message, decisions)
            priority: Queue priority (high/normal)
        """
        session, message, decisions = item

        try:
            # Generate response
            response = await self._generate_response(session, message, decisions)

            # Send response
            response_msg = WebSocketMessage(
                type=MessageType.RESPONSE, payload=response, reply_to=message.message_id
            )
            await self._send_to_session(session, response_msg)

            self.stats["messages_sent"] += 1

        except Exception as e:
            logger.error(f"Error processing queue item: {e}")
            self.stats["errors"] += 1

    async def _generate_response(
        self, session: WebSocketSession, message: WebSocketMessage, decisions: Dict
    ) -> Dict[str, Any]:
        """
        Generate AI response for message

        Args:
            session: WebSocket session
            message: WebSocket message
            decisions: Routing decisions

        Returns:
            Response payload
        """
        # Check cache first
        if self.cache_client:
            cache_key = f"response:{message.payload.get('content', '')}"
            cached_response = await self.cache_client.get(cache_key)
            if cached_response:
                return cached_response

        # Use MCP server if available
        if self.mcp_server and "agent" in decisions:
            agent_id = decisions["agent"].selected_option
            mcp_response = await self.mcp_server.process_message(
                session.user_id,
                message.payload.get("content", ""),
                agent_id=agent_id,
                session_id=session.session_id,
            )

            # Cache response
            if self.cache_client:
                await self.cache_client.set(cache_key, mcp_response)

            return mcp_response

        # Fallback: simple response
        return {
            "content": f"I received your message: {message.payload.get('content', '')}",
            "session_id": session.session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _handle_auth(self, session: WebSocketSession, message: WebSocketMessage):
        """
        Handle authentication message

        Args:
            session: WebSocket session
            message: WebSocket message
        """
        try:
            payload = message.payload
            token = payload.get("token")
            user_id = payload.get("user_id")

            # Validate token (simplified - in production, use proper auth)
            if not token or not user_id:
                raise ValueError("Missing token or user_id")

            # Update session state
            session.state = ConnectionState.AUTHENTICATED
            session.user_id = user_id
            session.metadata["auth_time"] = datetime.utcnow().isoformat()

            # Add to user sessions
            async with self._sessions_lock:
                self.user_sessions[user_id].add(session.session_id)

            # Send success response
            success_msg = WebSocketMessage(
                type=MessageType.RESPONSE,
                payload={
                    "status": "authenticated",
                    "user_id": user_id,
                    "session_id": session.session_id,
                    "capabilities": session.capabilities,
                },
                reply_to=message.message_id,
            )
            await self._send_to_session(session, success_msg)

            logger.info(
                f"Session authenticated: {session.session_id} for user {user_id}"
            )

        except Exception as e:
            logger.error(f"Authentication failed for {session.session_id}: {e}")
            self.stats["auth_failures"] += 1

            # Send error response
            error_msg = WebSocketMessage(
                type=MessageType.ERROR,
                payload={"error": "Authentication failed", "details": str(e)},
                reply_to=message.message_id,
            )
            await self._send_to_session(session, error_msg)

    async def _handle_subscribe(
        self, session: WebSocketSession, message: WebSocketMessage
    ):
        """
        Handle event subscription

        Args:
            session: WebSocket session
            message: WebSocket message
        """
        event_type = message.payload.get("event")
        if event_type:
            session.subscriptions.add(event_type)
            self.event_subscribers[event_type].add(session.session_id)

            success_msg = WebSocketMessage(
                type=MessageType.RESPONSE,
                payload={"status": "subscribed", "event": event_type},
                reply_to=message.message_id,
            )
            await self._send_to_session(session, success_msg)

    async def _handle_unsubscribe(
        self, session: WebSocketSession, message: WebSocketMessage
    ):
        """
        Handle event unsubscription

        Args:
            session: WebSocket session
            message: WebSocket message
        """
        event_type = message.payload.get("event")
        if event_type:
            session.subscriptions.discard(event_type)
            self.event_subscribers[event_type].discard(session.session_id)

            success_msg = WebSocketMessage(
                type=MessageType.RESPONSE,
                payload={"status": "unsubscribed", "event": event_type},
                reply_to=message.message_id,
            )
            await self._send_to_session(session, success_msg)

    async def _handle_ping(self, session: WebSocketSession, message: WebSocketMessage):
        """
        Handle ping message

        Args:
            session: WebSocket session
            message: WebSocket message
        """
        session.update_activity()

        pong_msg = WebSocketMessage(
            type=MessageType.PONG,
            payload={"timestamp": datetime.utcnow().isoformat()},
            reply_to=message.message_id,
        )
        await self._send_to_session(session, pong_msg)

    async def _send_to_session(
        self, session: WebSocketSession, message: WebSocketMessage
    ):
        """
        Send message to WebSocket session

        Args:
            session: WebSocket session
            message: WebSocket message to send
        """
        try:
            await session.websocket.send(json.dumps(message.to_dict()))
        except Exception as e:
            logger.error(f"Error sending to session {session.session_id}: {e}")
            raise

    async def _cleanup_session(self, session_id: str):
        """
        Clean up expired or disconnected session

        Args:
            session_id: Session ID to clean up
        """
        async with self._sessions_lock:
            session = self.sessions.pop(session_id, None)
            if session:
                # Remove from user sessions
                if session.user_id:
                    self.user_sessions[session.user_id].discard(session_id)
                    if not self.user_sessions[session.user_id]:
                        del self.user_sessions[session.user_id]

                # Remove from event subscribers
                for event_type in session.subscriptions:
                    self.event_subscribers[event_type].discard(session_id)

                self.stats["active_sessions"] = len(self.sessions)
                logger.info(f"Session cleaned up: {session_id}")

    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions"""
        while self._is_running:
            try:
                async with self._sessions_lock:
                    expired_sessions = [
                        session_id
                        for session_id, session in self.sessions.items()
                        if not session.is_active(timeout_minutes=self.session_timeout)
                    ]

                    for session_id in expired_sessions:
                        await self._cleanup_session(session_id)

                # Run cleanup every minute
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

    async def broadcast_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Broadcast event to all subscribers

        Args:
            event_type: Event type
            payload: Event payload
        """
        subscribers = self.event_subscribers.get(event_type, set())

        event_msg = WebSocketMessage(
            type=MessageType.EVENT,
            payload={
                "event": event_type,
                "data": payload,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        for session_id in subscribers:
            session = self.sessions.get(session_id)
            if session and session.is_active():
                try:
                    await self._send_to_session(session, event_msg)
                except Exception as e:
                    logger.error(f"Error broadcasting to {session_id}: {e}")

    async def send_notification(self, user_id: str, notification: Dict[str, Any]):
        """
        Send notification to specific user

        Args:
            user_id: User ID to send notification to
            notification: Notification payload
        """
        session_ids = self.user_sessions.get(user_id, set())

        notification_msg = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            payload={**notification, "timestamp": datetime.utcnow().isoformat()},
        )

        for session_id in session_ids:
            session = self.sessions.get(session_id)
            if session and session.is_active():
                try:
                    await self._send_to_session(session, notification_msg)
                except Exception as e:
                    logger.error(f"Error sending notification to {session_id}: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get gateway statistics"""
        return {
            **self.stats,
            "active_sessions": len(self.sessions),
            "unique_users": len(self.user_sessions),
            "event_subscribers": {
                event: len(sessions)
                for event, sessions in self.event_subscribers.items()
            },
            "queue_sizes": {
                "hot_queue": len(self.hot_queue),
                "cold_queue": len(self.cold_queue),
            },
            "is_running": self._is_running,
        }

    async def _get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user history from memory system"""
        if self.memory_system:
            try:
                return await self.memory_system.get_user_history(user_id)
            except Exception as e:
                logger.error(f"Error getting user history: {e}")
        return []

    async def _get_memory_context(self, user_id: str) -> Dict[str, Any]:
        """Get memory context for user"""
        if self.memory_system:
            try:
                return await self.memory_system.get_memory_context(user_id)
            except Exception as e:
                logger.error(f"Error getting memory context: {e}")
        return {}


# Convenience function for quick initialization
def create_websocket_gateway(
    host: str = "0.0.0.0", port: int = 18789, config: Dict[str, Any] = None
) -> WebSocketGateway:
    """Create configured WebSocket Gateway"""
    config = config or {}

    return WebSocketGateway(
        host=host,
        port=port,
        max_connections=config.get("max_connections", 100),
        session_timeout=config.get("session_timeout", 30),
        enable_mcp=config.get("enable_mcp", True),
        mcp_port=config.get("mcp_port", 18790),
    )


if __name__ == "__main__":
    # Example usage
    async def main():
        gateway = create_websocket_gateway()

        # Start gateway
        await gateway.start()

        # Start WebSocket server
        server = await websockets.serve(
            gateway.handle_connection, gateway.host, gateway.port
        )

        print(f"WebSocket Gateway running on ws://{gateway.host}:{gateway.port}")

        # Keep running
        await server.wait_closed()

    asyncio.run(main())
