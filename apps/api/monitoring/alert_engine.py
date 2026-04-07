"""
JEBAT Alert Engine

Alerting and notification system:
- Threshold-based alerts
- Custom alert rules
- Multiple notification channels
- Alert history
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Alert definition."""

    id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    message: str = ""
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertEngine:
    """
    Alert Engine for JEBAT.

    Manages alerting rules and notifications.
    """

    def __init__(self):
        """Initialize Alert Engine."""
        self.rules: List[Dict[str, Any]] = []
        self.alerts: List[Alert] = []
        self.notification_handlers: Dict[str, Callable] = {}

        logger.info("AlertEngine initialized")

    def register_notification_handler(
        self,
        channel: str,
        handler: Callable,
    ):
        """Register notification handler."""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler: {channel}")

    def add_rule(
        self,
        name: str,
        metric: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        channels: Optional[List[str]] = None,
    ):
        """
        Add alerting rule.

        Args:
            name: Rule name
            metric: Metric to monitor
            condition: Condition (>, <, ==, >=, <=)
            threshold: Threshold value
            severity: Alert severity
            channels: Notification channels
        """
        rule = {
            "id": f"rule_{name.lower().replace(' ', '_')}",
            "name": name,
            "metric": metric,
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "channels": channels or ["log"],
            "enabled": True,
        }

        self.rules.append(rule)

        logger.info(f"Added alert rule: {name}")

    async def check_alerts(
        self,
        metrics: Dict[str, float],
    ) -> List[Alert]:
        """
        Check metrics against alert rules.

        Args:
            metrics: Current metric values

        Returns:
            List of triggered alerts
        """
        triggered = []

        for rule in self.rules:
            if not rule["enabled"]:
                continue

            metric_value = metrics.get(rule["metric"])
            if metric_value is None:
                continue

            # Check condition
            triggered_alert = self._evaluate_condition(rule, metric_value)

            if triggered_alert:
                triggered.append(triggered_alert)
                await self._send_notifications(triggered_alert)

        return triggered

    def _evaluate_condition(
        self,
        rule: Dict[str, Any],
        value: float,
    ) -> Optional[Alert]:
        """Evaluate alert condition."""
        condition = rule["condition"]
        threshold = rule["threshold"]

        triggered = False

        if condition == ">" and value > threshold:
            triggered = True
        elif condition == "<" and value < threshold:
            triggered = True
        elif condition == ">=" and value >= threshold:
            triggered = True
        elif condition == "<=" and value <= threshold:
            triggered = True
        elif condition == "==" and value == threshold:
            triggered = True

        if triggered:
            alert = Alert(
                id=f"alert_{rule['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                name=rule["name"],
                severity=rule["severity"],
                message=f"{rule['name']}: {value} {condition} {threshold}",
                metadata={
                    "rule_id": rule["id"],
                    "metric": rule["metric"],
                    "value": value,
                    "threshold": threshold,
                },
            )

            self.alerts.append(alert)
            return alert

        return None

    async def _send_notifications(self, alert: Alert):
        """Send alert notifications."""
        for channel in ["log"]:  # Default to log
            if channel == "log":
                self._log_alert(alert)
            elif channel in self.notification_handlers:
                await self.notification_handlers[channel](alert)

    def _log_alert(self, alert: Alert):
        """Log alert."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }.get(alert.severity, logging.INFO)

        logger.log(
            log_level,
            f"[ALERT] {alert.name}: {alert.message}",
        )

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [a for a in self.alerts if a.status == AlertStatus.ACTIVE]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                return True
        return False

    def get_alert_history(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get alert history."""
        return [
            {
                "id": a.id,
                "name": a.name,
                "severity": a.severity.value,
                "status": a.status.value,
                "triggered_at": a.triggered_at.isoformat(),
                "message": a.message,
            }
            for a in sorted(self.alerts, key=lambda x: x.triggered_at, reverse=True)
        ][:limit]
