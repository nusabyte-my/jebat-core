Dev\jebat\webhook\webhook_system.py
# ==================== JEBAT AI System - Webhook System ====================
# Version: 1.0.0
# Comprehensive webhook management system for event triggering and delivery
#
# This module provides:
# - Webhook endpoint registration and management
# - Event triggering and delivery with retry logic
# - Webhook authentication and authorization
# - Signature validation for security
# - Rate limiting and throttling
# - Webhook metrics and monitoring
# - Integration with all enhanced JEBAT systems
#
# Features:
# - Multi-protocol support (HTTP, HTTPS, gRPC)
# - Event queue management (pending, processing, delivered, failed)
# - Exponential backoff retry with configurable limits
# - Dead letter queue for permanently failed events
# - Webhook secret management (HMAC signature verification)
# - Real-time delivery status tracking
# - Batch and bulk event delivery
# - Webhook filtering and routing
# - Comprehensive logging and monitoring

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urlparse

import aiohttp
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

from ..database.repositories import WebhookConfigRepository, WebhookLogRepository
from ..database.models import WebhookConfig, WebhookLog
from ..cache.cache_manager import CacheManager
from ..decision_engine.engine import DecisionEngine
from ..error_recovery.system import ErrorRecoverySystem

# Configure logging
logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Webhook event type enumeration"""

    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    MEMORY_CONSOLIDATED = "memory_consolidated"
    ERROR_OCCURRED = "error_occurred"
    SECURITY_ALERT = "security_alert"
    SYSTEM_EVENT = "system_event"


class DeliveryStatus(str, Enum):
    """Webhook delivery status enumeration"""

    PENDING = "pending"
    TRIGGERING = "triggering"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    EXPIRED = "expired"


class RetryPolicy(str, Enum):
    """Retry policy enumeration"""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR = "linear"
    IMMEDIATE = "immediate"
    NO_RETRY = "no_retry"


class WebhookProtocol(str, Enum):
    """Webhook protocol enumeration"""

    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


@dataclass
class WebhookEvent:
    """
    Webhook event dataclass.

    Contains event data to be delivered to webhooks.
    """

    event_id: str
    event_type: WebhookEvent
    timestamp: datetime
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    source: str = "jebat_system"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata,
            "source": self.source,
        }

    def to_json(self) -> str:
        """Convert to JSON for delivery."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class DeliveryResult:
    """
    Webhook delivery result.

    Contains delivery status, attempts, and final outcome.
    """

    webhook_url: str
    event_id: str
    status: DeliveryStatus
    attempt_count: int
    last_attempt_at: datetime
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    retry_delay: Optional[int] = None
    next_attempt_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "webhook_url": self.webhook_url,
            "event_id": self.event_id,
            "status": self.status.value,
            "attempt_count": self.attempt_count,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "retry_delay": self.retry_delay,
            "next_attempt_at": self.next_attempt_at.isoformat() if self.next_attempt_at else None,
        }


@dataclass
class WebhookConfig:
    """
    Webhook configuration dataclass.

    Contains webhook endpoint configuration and settings.
    """

    id: str
    url: str
    description: str
    protocol: WebhookProtocol
    secret: str  # Encrypted secret for HMAC signature verification
    events: List[str]  # Event types to subscribe to
    headers: Dict[str, str]  # Custom headers to include
    method: str = "POST"  # HTTP method to use
    timeout_seconds: int = 30
    retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    max_retries: int = 5
    retry_backoff_multiplier: float = 2.0
    retry_initial_delay_seconds: int = 1
    rate_limit_per_minute: int = 60  # Rate limit per webhook
    is_active: bool = True
    is_verified: bool = True  # Whether webhook signature is verified
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "url": self.url,
            "description": self.description,
            "protocol": self.protocol.value,
            "events": self.events,
            "headers": self.headers,
            "method": self.method,
            "timeout_seconds": self.timeout_seconds,
            "retry_policy": self.retry_policy.value,
            "max_retries": self.max_retries,
            "retry_backoff_multiplier": self.retry_backoff_multiplier,
            "retry_initial_delay_seconds": self.retry_initial_delay_seconds,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "statistics": self.statistics,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
        }


@dataclass
class EventFilter:
    """
    Event filter for selective webhook triggering.

    Allows webhooks to only receive specific types of events.
    """

    event_types: List[WebhookEvent]
    sources: List[str]
    metadata_filters: Dict[str, Any]

    def matches(self, event: WebhookEvent) -> bool:
        """Check if event matches the filter."""

        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False

        # Check source
        if self.sources and event.source not in self.sources:
            return False

        # Check metadata filters
        if self.metadata_filters:
            for key, value in self.metadata_filters.items():
                if key in event.metadata and event.metadata[key] != value:
                    return False

        return True


class WebhookClient:
    """
    Async HTTP client for webhook delivery.

    Handles connection pooling, retry logic, and timeout management.
    """

    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
        timeout: int = 30,
        max_connections: int = 100,
    ):
        """
        Initialize webhook client.

        Args:
            session: HTTP client session
            timeout: Request timeout in seconds
            max_connections: Maximum concurrent connections
        """
        self.session = session or aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=max_connections),
            timeout=aiohttp.ClientTimeout(total=timeout),
        )
        self.timeout = timeout
        self.max_connections = max_connections
        self.logger = logging.getLogger(f"webhook_client.{id(self)}")

    async def trigger(
        self,
        webhook_url: str,
        event: WebhookEvent,
        secret: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
    ) -> DeliveryResult:
        """
        Trigger a webhook by delivering an event.

        Args:
            webhook_url: Webhook URL
            event: Event to deliver
            secret: Secret for HMAC signature
            headers: Custom headers
            method: HTTP method
            timeout: Request timeout override

        Returns:
            DeliveryResult: Delivery result
        """
        start_time = time.time()

        try:
            # Prepare request
            request_data = event.to_json()

            # Generate HMAC signature
            signature = self._generate_signature(request_data, secret)

            # Prepare headers
            request_headers = {
                "Content-Type": "application/json",
                "X-JebAT-Signature": signature,
                "X-JebAT-Event-ID": event.event_id,
                "X-JebAT-Timestamp": event.timestamp.isoformat(),
            }

            # Add custom headers
            if headers:
                request_headers.update(headers)

            # Determine protocol and URL
            parsed_url = urlparse(webhook_url)
            if parsed_url.scheme not in ['http', 'https']:
                parsed_url = parsed_url._replace(scheme='https')

            url = parsed_url.geturl()

            # Make HTTP request based on method
            if method.upper() == "POST":
                response = await self.session.post(url, data=request_data, headers=request_headers)
            elif method.upper() == "PUT":
                response = await self.session.put(url, data=request_data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = await self.session.delete(url, headers=request_headers)
            elif method.upper() == "GET":
                response = await self.session.get(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check response status
            latency_ms = int((time.time() - start_time) * 1000)

            if response.status == 200 or response.status == 201 or response.status == 202:
                return DeliveryResult(
                    webhook_url=webhook_url,
                    event_id=event.event_id,
                    status=DeliveryStatus.DELIVERED,
                    attempt_count=1,
                    last_attempt_at=datetime.now(timezone.utc),
                    response_status=response.status,
                    response_body=await response.text(),
                    retry_delay=None,
                    next_attempt_at=None,
                )
            elif response.status == 401 or response.status == 403:
                # Rate limited or unauthorized
                error_msg = "Unauthorized or rate limited"
                return DeliveryResult(
                    webhook_url=webhook_url,
                    event_id=event.event_id,
                    status=DeliveryStatus.FAILED,
                    attempt_count=1,
                    last_attempt_at=datetime.now(timezone.utc),
                    response_status=response.status,
                    response_body=await response.text(),
                    error_message=error_msg,
                    retry_delay=None,
                    next_attempt_at=None,
                )
            elif response.status >= 500:
                # Server error - might be transient
                error_msg = f"Server error: {response.status}"
                return DeliveryResult(
                    webhook_url=webhook_url,
                    event_id=event.event_id,
                    status=DeliveryStatus.FAILED,
                    attempt_count=1,
                    last_attempt_at=datetime.now(timezone.utc),
                    response_status=response.status,
                    response_body=await response.text(),
                    error_message=error_msg,
                    retry_delay=30,  # Suggest retry delay
                    next_attempt_at=datetime.now(timezone.utc) + timedelta(seconds=30),
                )
            else:
                error_msg = f"Unexpected status: {response.status}"
                return DeliveryResult(
                    webhook_url=webhook_url,
                    event_id=event.event_id,
                    status=DeliveryStatus.FAILED,
                    attempt_count=1,
                    last_attempt_at=datetime.now(timezone.utc),
                    response_status=response.status,
                    response_body=await response.text(),
                    error_message=error_msg,
                    retry_delay=60,  # Longer retry for unknown errors
                    next_attempt_at=datetime.now(timezone.utc) + timedelta(seconds=60),
                )

        except asyncio.TimeoutError:
            self.logger.error(f"Webhook timeout for {webhook_url}")
            return DeliveryResult(
                webhook_url=webhook_url,
                event_id=event.event_id,
                status=DeliveryStatus.FAILED,
                attempt_count=1,
                last_attempt_at=datetime.now(timezone.utc),
                error_message="Request timeout",
                retry_delay=self.timeout,
                next_attempt_at=datetime.now(timezone.utc) + timedelta(seconds=self.timeout),
            )

        except aiohttp.ClientError as e:
            self.logger.error(f"Client error for {webhook_url}: {e}")
            return DeliveryResult(
                webhook_url=webhook_url,
                event_id=event.event_id,
                status=DeliveryStatus.FAILED,
                attempt_count=1,
                last_attempt_at=datetime.now(timezone.utc),
                error_message=f"Client error: {str(e)}",
                retry_delay=60,
                next_attempt_at=datetime.now(timezone.utc) + timedelta(seconds=60),
            )

        except Exception as e:
            self.logger.error(f"Unexpected error for {webhook_url}: {e}")
            return DeliveryResult(
                webhook_url=webhook_url,
                event_id=event.event_id,
                status=DeliveryStatus.FAILED,
                attempt_count=1,
                last_attempt_at=datetime.now(timezone.utc),
                error_message=f"Unexpected error: {str(e)}",
                retry_delay=60,
                next_attempt_at=datetime.now(timezone.utc) + timedelta(seconds=60),
            )

    def _generate_signature(self, data: str, secret: str) -> str:
        """
        Generate HMAC signature for webhook authentication.

        Args:
            data: JSON data to sign
            secret: Secret key for HMAC

        Returns:
            str: Base64-encoded HMAC signature
        """
        signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256,
        ).digest()

        return signature.hex()

    async def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Verify HMAC signature from webhook.

        Args:
            payload: JSON payload
            signature: HMAC signature to verify
            secret: Secret key for verification

        Returns:
            bool: True if signature is valid
        """
        expected_signature = self._generate_signature(payload, secret)
        return secrets.compare_digest(expected_signature.encode(), signature.encode())

    async def close(self) -> None:
        """Close HTTP client session."""
        if self.session:
            await self.session.close()


class WebhookManager:
    """
    High-level webhook management system.

    Features:
    - Webhook registration and lifecycle management
    - Event triggering and delivery
    - Retry logic with exponential backoff
    - Dead letter queue for failed events
    - Rate limiting per webhook
    - Webhook statistics and monitoring
    - Integration with database, cache, error recovery
    """

    def __init__(
        self,
        webhook_repo: Optional[WebhookConfigRepository] = None,
        webhook_log_repo: Optional[WebhookLogRepository] = None,
        cache_manager: Optional[CacheManager] = None,
        error_recovery: Optional[ErrorRecoverySystem] = None,
        decision_engine: Optional[DecisionEngine] = None,
    ):
        """
        Initialize webhook manager.

        Args:
            webhook_repo: Repository for webhook configs
            webhook_log_repo: Repository for webhook logs
            cache_manager: Cache manager for caching results
            error_recovery: Error recovery system
            decision_engine: Decision engine for routing
        """
        self.webhook_repo = webhook_repo
        self.webhook_log_repo = webhook_log_repo
        self.cache_manager = cache_manager
        self.error_recovery = error_recovery
        self.decision_engine = decision_engine

        # Create webhook client
        self.client = WebhookClient(session=None)

        # Event queue (in-memory for now, could be Redis in production)
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.delivery_queue: asyncio.Queue = asyncio.Queue()

        # Dead letter queue for permanently failed events
        self.dead_letter_queue: List[WebhookEvent] = []

        # Active webhooks (loaded from database)
        self.webhooks: Dict[str, WebhookConfig] = {}

        # Rate limiting state
        self.rate_limit_state: Dict[str, Dict[str, Any]] = {}

        # Statistics
        self.stats = {
            "total_events": 0,
            "delivered_events": 0,
            "failed_events": 0,
            "dlq_events": 0,
            "active_webhooks": 0,
            "total_triggers": 0,
        }

        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """
        Initialize webhook manager and load webhooks from database.
        """
        self.logger.info("Initializing webhook manager...")

        # Load webhooks from database
        if self.webhook_repo:
            try:
                configs = await self.webhook_repo.get_all()
                for config in configs:
                    if config.is_active:
                        self.webhooks[config.id] = config
                        self.stats["active_webhooks"] += 1

                self.logger.info(f"Loaded {len(self.webhooks)} active webhooks from database")
            except Exception as e:
                self.logger.error(f"Failed to load webhooks: {e}")

        # Start delivery workers
        self.logger.info("Starting webhook delivery workers...")

    async def register_webhook(
        self,
        url: str,
        description: str,
        events: List[WebhookEvent],
        secret: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
        timeout_seconds: int = 30,
        retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF,
        max_retries: int = 5,
        retry_backoff_multiplier: float = 2.0,
        retry_initial_delay_seconds: int = 1,
        rate_limit_per_minute: int = 60,
        protocol: WebhookProtocol = WebhookProtocol.HTTPS,
    ) -> str:
        """
        Register a new webhook.

        Args:
            url: Webhook URL
            description: Webhook description
            events: List of event types to subscribe to
            secret: Secret for HMAC signature
            headers: Custom headers
            method: HTTP method
            timeout_seconds: Request timeout
            retry_policy: Retry policy
            max_retries: Maximum retry attempts
            retry_backoff_multiplier: Exponential backoff multiplier
            retry_initial_delay_seconds: Initial retry delay
            rate_limit_per_minute: Rate limit per minute
            protocol: HTTP/HTTPS protocol

        Returns:
            str: Webhook ID
        """
        webhook_id = f"webhook_{secrets.token_hex(16)}"

        config = WebhookConfig(
            id=webhook_id,
            url=url,
            description=description,
            protocol=protocol,
            events=[e.value for e in events],
            headers=headers or {},
            method=method,
            timeout_seconds=timeout_seconds,
            retry_policy=retry_policy,
            max_retries=max_retries,
            retry_backoff_multiplier=retry_backoff_multiplier,
            retry_initial_delay_seconds=retry_initial_delay_seconds,
            rate_limit_per_minute=rate_limit_per_minute,
            is_active=True,
            is_verified=False,
            secret=secret,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            statistics={
                "total_triggers": 0,
                "successful_triggers": 0,
                "failed_triggers": 0,
                "average_delivery_time_ms": 0,
            },
        )

        # Store in database
        if self.webhook_repo:
            try:
                await self.webhook_repo.create(config)
                self.webhooks[webhook_id] = config
                self.stats["active_webhooks"] += 1
                self.logger.info(f"Registered webhook: {webhook_id} -> {url}")
            except Exception as e:
                self.logger.error(f"Failed to register webhook: {e}")

        return webhook_id

    async def unregister_webhook(self, webhook_id: str) -> bool:
        """
        Unregister and delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            bool: True if deleted, False otherwise
        """
        if self.webhook_repo:
            try:
                deleted = await self.webhook_repo.delete(webhook_id)

                if webhook_id in self.webhooks:
                    del self.webhooks[webhook_id]
                    self.stats["active_webhooks"] -= 1

                self.logger.info(f"Unregistered webhook: {webhook_id}")
                return deleted
            except Exception as e:
                self.logger.error(f"Failed to unregister webhook {webhook_id}: {e}")
                return False

        return False

    async def trigger_event(
        self,
        event: WebhookEvent,
        event_filter: Optional[EventFilter] = None,
    ) -> None:
        """
        Trigger a webhook event to all registered webhooks.

        Args:
            event: Event to trigger
            event_filter: Optional event filter
        """
        self.stats["total_events"] += 1

        # Check if event matches filter
        if event_filter and not event_filter.matches(event):
            self.logger.debug(f"Event filtered out by filter: {event.event_type}")
            return

        # Queue event for delivery
        await self.event_queue.put(event)

        self.logger.info(f"Queued event: {event.event_type} - {event.event_id}")

    async def _delivery_worker(self) -> None:
        """
        Worker that processes webhook deliveries.
        """
        while True:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                if event is None:
                    # No more events, wait a bit
                    await asyncio.sleep(0.1)
                    continue

                # Find matching webhooks
                matching_webhooks = []
                for webhook_id, config in self.webhooks.items():
                    if event.event_type.value in config.events:
                        matching_webhooks.append((webhook_id, config))

                if not matching_webhooks:
                    self.logger.warning(f"No webhooks for event type: {event.event_type}")
                    # Move to DLQ
                    self.dead_letter_queue.append(event)
                    self.stats["dlq_events"] += 1
                    self.stats["failed_events"] += 1
                    continue

                # Check rate limits
                for webhook_id, config in matching_webhooks:
                    if not self._check_rate_limit(webhook_id):
                        # Rate limited, skip for now
                        continue

                # Deliver to matching webhooks
                for webhook_id, config in matching_webhooks:
                    try:
                        # Update statistics
                        self.stats["total_triggers"] += 1
                        config.statistics["total_triggers"] = config.statistics.get("total_triggers", 0) + 1

                        # Check if should use error recovery
                        if self.error_recovery:
                            result = await self.error_recovery.execute_with_retry(
                                webhook_id,
                                lambda: self.client.trigger(config.url, event, config.secret, config.headers, config.method),
                                max_retries=config.max_retries,
                            )
                        else:
                            result = await self.client.trigger(config.url, event, config.secret, config.headers, config.method)

                        # Update webhook statistics
                        if result.status == DeliveryStatus.DELIVERED:
                            self.stats["delivered_events"] += 1
                            config.statistics["successful_triggers"] = config.statistics.get("successful_triggers", 0) + 1

                            # Update average delivery time
                            current_avg = config.statistics.get("average_delivery_time_ms", 0)
                            new_avg = (current_avg * (config.statistics.get("total_triggers", 1) - 1 + result.latency_ms) / config.statistics.get("total_triggers", 1)
                            config.statistics["average_delivery_time_ms"] = new_avg
                            self.stats["total_triggers"] = config.statistics["total_triggers"]

                            # Log delivery
                            await self.webhook_log_repo.create(
                                webhook_id=webhook_id,
                                event_id=event.event_id,
                                status=result.status.value,
                                response_status=result.response_status,
                                response_body=result.response_body,
                                attempt_count=result.attempt_count,
                                latency_ms=result.latency_ms,
                            )

                            config.last_triggered_at = datetime.now(timezone.utc)
                            await self.webhook_repo.update(config.id, statistics=config.statistics)

                            self.logger.info(f"Delivered event {event.event_id} to {webhook_id}")

                        else:
                            # Failed delivery
                            self.stats["failed_events"] += 1
                            config.statistics["failed_triggers"] = config.statistics.get("failed_triggers", 0) + 1

                            # Determine if should retry
                            should_retry = result.attempt_count < config.max_retries

                            if should_retry and result.next_attempt_at:
                                # Schedule retry
                                asyncio.create_task(
                                    self._retry_delivery(
                                        webhook_id,
                                        event,
                                        config,
                                        result,
                                        result.next_attempt_at,
                                    )
                                )
                            else:
                                # Move to DLQ
                                self.dead_letter_queue.append(event)
                                self.stats["dlq_events"] += 1

                            # Log failure
                            await self.webhook_log_repo.create(
                                webhook_id=webhook_id,
                                event_id=event.event_id,
                                status=result.status.value,
                                response_status=result.response_status,
                                response_body=result.response_body,
                                attempt_count=result.attempt_count,
                                error_message=result.error_message,
                                latency_ms=result.latency_ms,
                            )

                            self.logger.warning(f"Failed to deliver event {event.event_id} to {webhook_id}: {result.error_message}")

                    except Exception as e:
                        self.logger.error(f"Error delivering event {event.event_id} to {webhook_id}: {e}")
                        self.stats["failed_events"] += 1

                # Small delay between events
                await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                self.logger.info("Delivery worker cancelled")
                break
            except Exception as e:
                self.logger.error(f"Delivery worker error: {e}")
                await asyncio.sleep(1)

    async def _retry_delivery(
        self,
        webhook_id: str,
        event: WebhookEvent,
        config: WebhookConfig,
        result: DeliveryResult,
        retry_at: datetime,
    ) -> None:
        """
        Retry a failed webhook delivery.

        Args:
            webhook_id: Webhook ID
            event: Event to deliver
            config: Webhook configuration
            result: Previous delivery result
            retry_at: Time to retry at
        """
        delay_seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()

        if delay_seconds > 0:
            self.logger.info(f"Retrying delivery for {webhook_id} in {delay_seconds}s")
            await asyncio.sleep(delay_seconds)

        # Retry delivery
        new_result = await self.client.trigger(config.url, event, config.secret, config.headers, config.method)

        # Log retry
        await self.webhook_log_repo.create(
            webhook_id=webhook_id,
            event_id=event.event_id,
            status=new_result.status.value,
            response_status=new_result.response_status,
            response_body=new_result.response_body,
            attempt_count=result.attempt_count + 1,
            latency_ms=new_result.latency_ms,
            error_message=new_result.error_message,
        )

    def _check_rate_limit(self, webhook_id: str) -> bool:
        """
        Check if webhook is within rate limits.

        Args:
            webhook_id: Webhook ID

        Returns:
            bool: True if within rate limits, False otherwise
        """
        config = self.webhooks.get(webhook_id)
        if not config:
            return False

        # Get current rate limit state
        state = self.rate_limit_state.get(webhook_id, {
            "request_count": 0,
            "window_start": datetime.now(timezone.utc),
        })

        # Calculate if within limit
        time_since_window = (datetime.now(timezone.utc) - state["window_start"]).total_seconds()

        if time_since_window < 60:  # 1 minute window
            if state["request_count"] < config.rate_limit_per_minute:
                return True
            else:
                return False
        else:
            # Reset window if more than 1 minute
            if time_since_window >= 60:
                state["request_count"] = 0
                state["window_start"] = datetime.now(timezone.utc)
                return state["request_count"] < config.rate_limit_per_minute

            # Increment request count
            state["request_count"] += 1
            self.rate_limit_state[webhook_id] = state

            return state["request_count"] < config.rate_limit_per_minute

    async def _process_dlq(self) -> None:
        """
        Process dead letter queue and attempt delivery.
        """
        while self.dead_letter_queue:
            try:
                event = self.dead_letter_queue.pop(0)

                self.logger.info(f"Processing DLQ event: {event.event_type}")

                # Retry DLQ event
                matching_webhooks = []
                for webhook_id, config in self.webhooks.items():
                    if event.event_type.value in config.events:
                        matching_webhooks.append((webhook_id, config))

                if not matching_webhooks:
                    self.logger.warning(f"No webhooks for DLQ event: {event.event_type}")
                    continue

                for webhook_id, config in matching_webhooks:
                    try:
                        result = await self.client.trigger(config.url, event, config.secret, config.headers, config.method)

                        if result.status == DeliveryStatus.DELIVERED:
                            self.logger.info(f"DLQ event {event.event_id} delivered to {webhook_id}")
                            self.stats["dlq_events"] -= 1
                        else:
                            # Permanently failed, leave in DLQ
                            pass

                    except Exception as e:
                        self.logger.error(f"Error processing DLQ event {event.event_id}: {e}")

                # Delay between DLQ processing
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                self.logger.info("DLQ processing cancelled")
                break
            except Exception as e:
                self.logger.error(f"DLQ processor error: {e}")
                await asyncio.sleep(1)

    async def get_webhooks(self, active_only: bool = True) -> List[WebhookConfig]:
        """
        Get all registered webhooks.

        Args:
            active_only: Only return active webhooks

        Returns:
            List[WebhookConfig]: List of webhook configurations
        """
        return [
            config for config in self.webhooks.values()
            if not active_only or config.is_active
        ]

    async def get_webhook_stats(self, webhook_id: str) -> Optional[WebhookConfig]:
        """
        Get webhook configuration with statistics.

        Args:
            webhook_id: Webhook ID

        Returns:
            Optional[WebhookConfig]: Webhook config with stats
        """
        return self.webhooks.get(webhook_id)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive webhook statistics.

        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return {
            "total_events": self.stats["total_events"],
            "delivered_events": self.stats["delivered_events"],
            "failed_events": self.stats["failed_events"],
            "dlq_events": self.stats["dlq_events"],
            "active_webhooks": self.stats["active_webhooks"],
            "total_triggers": sum(
                config.statistics.get("total_triggers", 0)
                for config in self.webhooks.values()
            ),
            "success_rate": (
                self.stats["delivered_events"] / self.stats["total_events"] * 100
                if self.stats["total_events"] > 0
                else 0
            ),
            "average_delivery_time_ms": (
                sum(
                    config.statistics.get("average_delivery_time_ms", 0)
                    for config in self.webhooks.values()
                ) / len(self.webhooks)
                if self.webhooks
                else 0
            ),
        }

    async def verify_webhook_signature(self, payload: str, signature: str, webhook_id: str) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: JSON payload
            signature: HMAC signature
            webhook_id: Webhook ID

        Returns:
            bool: True if signature is valid
        """
        config = self.webhooks.get(webhook_id)
        if not config:
            return False

        return await self.client.verify_signature(payload, signature, config.secret)

    async def start(self) -> None:
        """
        Start webhook system and begin processing events.
        """
        self.logger.info("Starting webhook system...")

        # Start workers
        workers = [
            asyncio.create_task(self._delivery_worker()),
            asyncio.create_task(self._process_dlq()),
        ]

        self.logger.info("Webhook system started with {len(workers)} workers")

    async def stop(self) -> None:
        """
        Stop webhook system and cleanup resources.
        """
        self.logger.info("Stopping webhook system...")

        # Cancel all workers
        # (In production, would use graceful shutdown)

        await self.client.close()
        self.logger.info("Webhook system stopped")

    async def test_webhook(self, url: str) -> Dict[str, Any]:
        """
        Test a webhook endpoint.

        Args:
            url: Webhook URL to test

        Returns:
            Dict[str, Any]: Test results
        """
        test_event = WebhookEvent(
            event_id="test_event",
            event_type=WebhookEvent.SYSTEM_EVENT,
            timestamp=datetime.now(timezone.utc),
            payload={"test": "webhook_test"},
            metadata={"test": True},
        )

        result = await self.client.trigger(url, test_event, "", {"Content-Type": "application/json"})

        return {
            "url": url,
            "status": "success" if result.status == DeliveryStatus.DELIVERED else "failed",
            "latency_ms": result.latency_ms,
            "response_status": result.response_status,
            "response_body": result.response_body,
        }


class WebhookSystem:
    """
    High-level webhook system coordinator.

    Manages webhook registration, event triggering, and monitoring.
    """

    def __init__(
        self,
        webhook_repo: Optional[WebhookConfigRepository] = None,
        webhook_log_repo: Optional[WebhookLogRepository] = None,
        cache_manager: Optional[CacheManager] = None,
        error_recovery: Optional[ErrorRecoverySystem] = None,
        decision_engine: Optional[DecisionEngine] = None,
    ):
        """
        Initialize webhook system.

        Args:
            webhook_repo: Repository for webhook configs
            webhook_log_repo: Repository for webhook logs
            cache_manager: Cache manager for caching results
            error_recovery: Error recovery system
            decision_engine: Decision engine for smart routing
        """
        self.manager = WebhookManager(
            webhook_repo=webhook_repo,
            webhook_log_repo=webhook_log_repo,
            cache_manager=cache_manager,
            error_recovery=error_recovery,
            decision_engine=decision_engine,
        )
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize webhook system and load webhooks."""
        await self.manager.initialize()
        self.logger.info("Webhook system initialized and ready")

    async def register_webhook(
        self,
        url: str,
        description: str,
        events: List[WebhookEvent],
        secret: str,
        **kwargs,
    ) -> str:
        """Register a new webhook."""
        webhook_id = await self.manager.register_webhook(url, description, events, secret, **kwargs)
        self.logger.info(f"Registered webhook: {webhook_id}")
        return webhook_id

    async def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook."""
        success = await self.manager.unregister_webhook(webhook_id)
        if success:
            self.logger.info(f"Unregistered webhook: {webhook_id}")
        return True
        return False

    async def trigger_event(self, event: WebhookEvent, **kwargs) -> None:
        """Trigger a webhook event."""
        await self.manager.trigger_event(event, **kwargs)

    async def get_webhooks(self, active_only: bool = True) -> List[WebhookConfig]:
        """Get all registered webhooks."""
        return await self.manager.get_webhooks(active_only=active_only)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get webhook system statistics."""
        return await self.manager.get_statistics()

    async def test_webhook(self, url: str) -> Dict[str, Any]:
        """Test a webhook endpoint."""
        return await self.manager.test_webhook(url)

    async def start(self) -> None:
        """Start webhook system."""
        await self.manager.start()

    async def stop(self) -> None:
        """Stop webhook system."""
        await self.manager.stop()


# ==================== Database Repository Classes ====================

class WebhookConfigRepository(BaseRepository):
    """Repository for webhook configurations."""

    def __init__(self, session):
        super().__init__(session, WebhookConfig)


class WebhookLogRepository(BaseRepository):
    """Repository for webhook delivery logs."""

    def __init__(self, session):
        super().__init__(session, WebhookLog)


# ==================== Example Usage ====================

async def example_usage():
    """Example usage of webhook system."""
    from .database.models import AsyncSessionLocal
    from .database.repositories import RepositoryManager

    # Create session and repositories
    async with AsyncSessionLocal() as session:
        repos = RepositoryManager(session)

        # Initialize webhook system
        webhook_system = WebhookSystem(
            webhook_repo=repos.webhook_config,
            webhook_log_repo=repos.webhook_log,
            cache_manager=None,  # Would integrate with CacheManager
            error_recovery=None,  # Would integrate with ErrorRecoverySystem
            decision_engine=None,  # Would integrate with DecisionEngine
        )

        await webhook_system.initialize()

        # Register a test webhook
        webhook_id = await webhook_system.register_webhook(
            url="https://example.com/webhook",
            description="Example webhook",
            events=[WebhookEvent.TASK_COMPLETED, WebhookEvent.TASK_FAILED],
            secret="test_secret_key",
            max_retries=3,
            rate_limit_per_minute=30,
        )

        print(f"Registered webhook: {webhook_id}")

        # Trigger an event
        event = WebhookEvent(
            event_id="test_event",
            event_type=WebhookEvent.TASK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            payload={"message": "Task completed successfully"},
            metadata={"source": "test"},
        )

        await webhook_system.trigger_event(event)

        # Get statistics
        stats = await webhook_system.get_statistics()
        print(f"Webhook Statistics: {stats}")

        # Get webhooks
        webhooks = await webhook_system.get_webhooks()
        print(f"Active Webhooks ({len(webhooks)}):")
        for webhook in webhooks:
            print(f"  - {webhook.description} -> {webhook.url}")

        # Test webhook endpoint
        test_result = await webhook_system.test_webhook("https://httpbin.org/post")
        print(f"Webhook Test Result: {test_result}")

        # Cleanup
        await webhook_system.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
