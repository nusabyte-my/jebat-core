"""
JEBAT Enhanced Logging System

Structured logging with JSON output, log aggregation, and alert rules.

Features:
- Structured JSON logging
- Log levels and filtering
- Context injection
- Log rotation
- Alert rules engine
- Integration with ELK/Loki

Usage:
    from jebat.logging import get_logger, setup_logging

    setup_logging(level="INFO", format="json")
    logger = get_logger("my_module")

    logger.info("User logged in", extra={"user_id": "123", "action": "login"})
    logger.error("Database error", extra={"error": "connection refused"})
"""

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "thread",
                "threadName",
            ]:
                try:
                    json.dumps(value)  # Check if JSON serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        return json.dumps(log_data)


class ContextFilter(logging.Filter):
    """Add context to log records"""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to record"""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console: bool = True,
) -> logging.Logger:
    """
    Setup enhanced logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format (json, text)
        log_file: Optional log file path
        max_bytes: Max log file size before rotation
        backup_count: Number of backup files to keep
        console: Enable console output

    Returns:
        Root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Add context filter
    context = {
        "app": "jebat",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
    root_logger.addFilter(ContextFilter(context))

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class AlertRule:
    """Log alert rule"""

    def __init__(
        self,
        name: str,
        condition: callable,
        action: callable,
        cooldown: int = 300,  # 5 minutes
    ):
        """
        Initialize alert rule.

        Args:
            name: Rule name
            condition: Function that takes log record and returns bool
            action: Function to call when condition is met
            cooldown: Seconds between alerts
        """
        self.name = name
        self.condition = condition
        self.action = action
        self.cooldown = cooldown
        self.last_triggered = 0

    def check(self, record: logging.LogRecord) -> bool:
        """Check if rule should trigger"""
        import time

        if self.condition(record):
            current_time = time.time()
            if current_time - self.last_triggered > self.cooldown:
                self.action(record)
                self.last_triggered = current_time
                return True
        return False


class AlertHandler(logging.Handler):
    """Logging handler with alert rules"""

    def __init__(self):
        super().__init__()
        self.rules = []

    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules.append(rule)

    def emit(self, record: logging.LogRecord):
        """Check alert rules"""
        for rule in self.rules:
            try:
                rule.check(record)
            except Exception as e:
                print(f"Alert rule {rule.name} failed: {e}")


# Example alert rules


def high_error_rate_rule(threshold: int = 10, cooldown: int = 60):
    """
    Create alert rule for high error rate.

    Args:
        threshold: Number of errors to trigger alert
        cooldown: Cooldown in seconds
    """
    error_count = [0]

    def condition(record: logging.LogRecord) -> bool:
        if record.levelno >= logging.ERROR:
            error_count[0] += 1
            return error_count[0] >= threshold
        return False

    def action(record: logging.LogRecord):
        print(f"ALERT: High error rate detected! ({error_count[0]} errors)")
        error_count[0] = 0

    return AlertRule("high_error_rate", condition, action, cooldown)


def specific_error_rule(error_pattern: str, cooldown: int = 300):
    """
    Create alert rule for specific error pattern.

    Args:
        error_pattern: Pattern to match in error message
        cooldown: Cooldown in seconds
    """

    def condition(record: logging.LogRecord) -> bool:
        if record.levelno >= logging.ERROR:
            return error_pattern in record.getMessage()
        return False

    def action(record: logging.LogRecord):
        print(f"ALERT: Specific error detected: {error_pattern}")

    return AlertRule(f"error_{error_pattern}", condition, action, cooldown)


# Usage example

if __name__ == "__main__":
    # Setup logging
    setup_logging(
        level="DEBUG",
        format="json",
        log_file=Path("logs/jebat.log"),
        console=True,
    )

    # Get logger
    logger = get_logger(__name__)

    # Add alert handler
    alert_handler = AlertHandler()
    alert_handler.add_rule(high_error_rate_rule(threshold=3))
    alert_handler.add_rule(specific_error_rule("database"))
    logging.getLogger().addHandler(alert_handler)

    # Test logging
    logger.info("Application started", extra={"user_id": "123"})
    logger.debug("Debug information", extra={"debug_data": {"key": "value"}})
    logger.warning("This is a warning")
    logger.error("This is an error")

    # Test alert
    for i in range(5):
        logger.error(f"Test error {i}")
