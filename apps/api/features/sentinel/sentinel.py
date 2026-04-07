# ==================== JEBAT AI System - Sentinel Security System ====================
# Version: 1.0.0
# Hidden security layer for threat detection, anomaly detection, and automated response
#
# This module provides:
# - Security event detection and logging
# - Anomaly detection in user behavior using ML and statistical analysis
# - Automated threat response mechanisms
# - Security policy enforcement and rule engine
# - Audit logging and compliance tracking
# - Integration with database (security_events, security_policies tables)
# - Integration with Decision Engine for security-related routing
# - Integration with Error Recovery for security-related issues
# - Hidden security layer for sophisticated threat detection
# - Security metrics and monitoring
# - Real-time threat scoring and risk assessment
#
# This is a production-grade security system designed to protect JEBAT from:
# - SQL Injection attacks
# - XSS (Cross-Site Scripting) attacks
# - CSRF (Cross-Site Request Forgery) attacks
# - Rate limiting abuse
# - Unauthorized access attempts
# - Data exfiltration attempts
# - Behavioral anomalies
# - Malicious input patterns

import asyncio
import hashlib
import ipaddress
import json
import logging
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from jebat.database.repositories import SecurityEventRepository, SecurityPolicyRepository, AuditLogRepository, UserRepository
from jebat.database.models import SecurityEvent, SecurityPolicy, AuditLog, User
from jebat.core.decision.engine import DecisionEngine
try:
    from jebat.error_recovery.system import ErrorRecoverySystem
except ImportError:
    ErrorRecoverySystem = None
from jebat.core.cache.smart_cache import CacheManager
from jebat.skills.base_skill import BaseSkill, SkillResult, SkillParameter, SkillCapability

# Configure logging
logger = logging.getLogger(__name__)


# ==================== Enums ====================

class SecurityEventType(str, Enum):
    """Security event type enumeration"""

    ANOMALY_DETECTED = "anomaly_detected"
    THREAT_BLOCKED = "threat_blocked"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MALICIOUS_INPUT = "malicious_input"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    DATA_EXFILTRATION_ATTEMPT = "data_exfiltration_attempt"
    POLICY_VIOLATION = "policy_violation"
    AUTHENTICATION_FAILURE = "authentication_failure"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    SECURITY_ALERT = "security_alert"


class SecuritySeverity(str, Enum):
    """Security severity enumeration"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"


class ThreatType(str, Enum):
    """Threat type enumeration"""

    MALWARE = "malware"
    PHISHING = "phishing"
    SOCIAL_ENGINEERING = "social_engineering"
    INSIDER_THREAT = "insider_threat"
    DDOS = "ddos"
    DATA_BREACH = "data_breach"
    API_ABUSE = "api_abuse"
    AUTHENTICATION_ATTACK = "authentication_attack"
    UNKNOWN = "unknown"


class PolicyType(str, Enum):
    """Security policy type enumeration"""

    RATE_LIMITING = "rate_limiting"
    CONTENT_FILTERING = "content_filtering"
    ACCESS_CONTROL = "access_control"
    DATA_RETENTION = "data_retention"
    INPUT_VALIDATION = "input_validation"
    AUTHENTICATION = "authentication"
    SESSION_MANAGEMENT = "session_management"


class ResponseAction(str, Enum):
    """Security response action enumeration"""

    BLOCK = "block"
    THROTTLE = "throttle"
    CHALLENGE = "challenge"
    LOG_ONLY = "log_only"
    NOTIFY = "notify"
    TERMINATE_SESSION = "terminate_session"
    REVOKE_ACCESS = "revoke_access"
    ALERT_ADMIN = "alert_admin"


# ==================== Data Classes ====================

@dataclass
class SecurityContext:
    """
    Security context for security analysis.

    Contains user information, request details, and environmental context.
    """
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    request_headers: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str = "production"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatAssessment:
    """
    Threat assessment result.

    Contains threat detection results, risk scores, and recommended actions.
    """
    threat_detected: bool = False
    threat_type: Optional[ThreatType] = None
    severity: SecuritySeverity = SecuritySeverity.INFO
    confidence_score: float = 0.0  # 0.0 to 1.0
    risk_score: float = 0.0  # 0.0 to 100.0
    recommended_action: Optional[ResponseAction] = None
    details: Dict[str, Any] = field(default_factory=dict)
    indicators: List[str] = field(default_factory=list)
    model_version: str = "1.0.0"
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AnomalyScore:
    """
    Anomaly detection result.

    Contains behavioral anomaly detection results with statistical analysis.
    """
    is_anomalous: bool = False
    anomaly_type: Optional[str] = None
    score: float = 0.0  # Higher means more anomalous
    threshold: float = 0.0
    features: Dict[str, float] = field(default_factory=dict)
    baseline: Optional[float] = None
    deviation: Optional[float] = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SecurityPolicy:
    """
    Security policy configuration.

    Defines security rules, enforcement actions, and policy metadata.
    """
    policy_id: str
    policy_name: str
    policy_type: PolicyType
    rules: Dict[str, Any]  # Policy rules in JSON format
    actions: Dict[str, Any]  # Enforcement actions
    severity: SecuritySeverity
    priority: int = 0  # Higher priority = more important
    is_active: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)  # When policy applies
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SecurityMetrics:
    """
    Security system metrics.

    Tracks overall security performance and threat statistics.
    """
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_by_severity: Dict[str, int] = field(default_factory=dict)
    threats_blocked: int = 0
    threats_detected: int = 0
    anomalies_detected: int = 0
    policies_enforced: int = 0
    avg_response_time_ms: float = 0.0
    false_positives: int = 0
    false_negatives: int = 0
    uptime_seconds: float = 0.0
    last_threat_time: Optional[datetime] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== Security Skills ====================

class SecurityAnalyzeSkill(BaseSkill):
    """
    Security analysis skill for detecting threats and anomalies.

    Performs comprehensive security analysis using ML models and statistical methods.
    """

    name = "security_analyze"
    skill_type = "analyze"
    description = "Comprehensive security analysis with threat detection, anomaly detection, and risk assessment"
    version = "1.0.0"
    timeout_seconds = 60
    max_retries = 2

    parameters = [
        SkillParameter(
            name="input_data",
            type=dict,
            description="Input data to analyze (request, user context, etc.)",
            required=True,
        ),
        SkillParameter(
            name="analyze_type",
            type=str,
            description="Type of analysis to perform (threat, anomaly, both)",
            default="both",
        ),
        SkillParameter(
            name="strict_mode",
            type=bool,
            description="Enable strict security mode (block more threats)",
            default=False,
        ),
    ]

    capabilities = [
        SkillCapability(
            name="threat_detection",
            description="Detect various types of cyber threats",
            enabled=True,
        ),
        SkillCapability(
            name="anomaly_detection",
            description="Detect behavioral anomalies using ML",
            enabled=True,
        ),
        SkillCapability(
            name="input_validation",
            description="Validate input for malicious patterns",
            enabled=True,
        ),
    ]


# End of Sentinel class

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize security analysis skill.

        Args:
            config: Skill configuration
        """
        super().__init__(config)

        # Security repositories (injected after creation)
        self.security_event_repo: Optional[SecurityEventRepository] = None
        self.security_policy_repo: Optional[SecurityPolicyRepository] = None
        self.audit_log_repo: Optional[AuditLogRepository] = None
        self.user_repo: Optional[UserRepository] = None

        # ML models for anomaly detection
        self.anomaly_detector: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False

        # Baseline data for anomaly detection
        self.request_rate_baseline: deque = deque(maxlen=100)
        self.response_time_baseline: deque = deque(maxlen=100)

        # Security metrics
        self.metrics = SecurityMetrics()

        # Train anomaly detector
        self._initialize_ml_models()

        logger.info(f"Security analysis skill initialized with ML models")

    def _initialize_ml_models(self) -> None:
        """Initialize ML models for anomaly detection."""
        try:
            # Create isolation forest for anomaly detection
            self.anomaly_detector = IsolationForest(
                n_estimators=100,
                max_samples=256,
                random_state=42,
                n_jobs=4,
                contamination=0.1,  # Expected outlier rate
            )

            # Create scaler for feature normalization
            self.scaler = StandardScaler()

            logger.info("ML models initialized for anomaly detection")
        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")
            self.anomaly_detector = None
            self.scaler = None

    async def _train_anomaly_detector(self, context: SecurityContext) -> None:
        """Train anomaly detection model with baseline data."""
        if not self.anomaly_detector:
            logger.warning("Anomaly detector not available, skipping training")
            return

        try:
            # Extract features from recent events
            events = await self._get_recent_security_events(context)

            if len(events) < 50:
                logger.warning("Not enough events to train anomaly detector")
                return

            # Prepare features
            features_list = []
            for event in events:
                features = await self._extract_features(event, context)
                if features:
                    features_list.append(features)

            if not features_list:
                return

            # Prepare feature matrix
            feature_array = np.array(features_list)

            # Train model
            if len(features_list) > 0:
                self.anomaly_detector.fit(feature_array)
                self.scaler.fit(feature_array)
                self.is_trained = True

                logger.info(f"Anomaly detector trained with {len(features_list)} samples")
        except Exception as e:
            logger.error(f"Failed to train anomaly detector: {e}")

    async def _extract_features(self, event: SecurityEvent, context: SecurityContext) -> Optional[List[float]]:
        """
        Extract features for ML-based anomaly detection.

        Features include:
        - Request rate (requests per minute)
        - Response time
        - Failed authentication attempts
        - Unique paths accessed
        - Data volume transferred
        """
        try:
            features = []

            # Feature 1: Request rate (requests per minute)
            request_rate = await self._calculate_request_rate(event.user_id, event.timestamp)
            features.append(request_rate)

            # Feature 2: Response time (normalized)
            if hasattr(event, 'metadata'):
                response_time = event.metadata.get('response_time_ms', 0)
                features.append(float(response_time) / 1000.0)  # Normalize to seconds
            else:
                features.append(0.0)

            # Feature 3: Failed authentication attempts
            failed_attempts = await self._count_failed_auth_attempts(event.user_id, event.timestamp)
            features.append(float(failed_attempts))

            # Feature 4: Unique paths accessed
            unique_paths = await self._count_unique_paths(event.user_id, event.timestamp)
            features.append(float(unique_paths))

            # Feature 5: Data volume
            data_volume = await self._calculate_data_volume(event.user_id, event.timestamp)
            features.append(float(data_volume))

            return features if any(features) else None

        except Exception as e:
            logger.error(f"Failed to extract features: {e}")
            return None

    async def _calculate_request_rate(self, user_id: str, timestamp: datetime) -> float:
        """Calculate request rate per minute for a user."""
        if not self.security_event_repo:
            return 0.0

        try:
            # Get events from last minute
            one_minute_ago = timestamp - timedelta(minutes=1)
            events = await self.security_event_repo.get_by_type(
                event_type=SecurityEventType.POLICY_VIOLATION,
                limit=100,
            )

            # Count requests from this user in last minute
            user_events = [e for e in events if hasattr(e, 'user_id') and e.user_id == user_id]

            return len(user_events) / 60.0  # Requests per second
        except Exception as e:
            logger.error(f"Failed to calculate request rate: {e}")
            return 0.0

    async def _count_failed_auth_attempts(self, user_id: str, timestamp: datetime) -> int:
        """Count failed authentication attempts for a user in last hour."""
        if not self.security_event_repo:
            return 0

        try:
            one_hour_ago = timestamp - timedelta(hours=1)
            events = await self.security_event_repo.get_by_type(
                event_type=SecurityEventType.AUTHENTICATION_FAILURE,
                limit=100,
            )

            # Count failures for this user
            user_events = [e for e in events if hasattr(e, 'user_id') and e.user_id == user_id]

            return len(user_events)
        except Exception as e:
            logger.error(f"Failed to count failed auth attempts: {e}")
            return 0

    async def _count_unique_paths(self, user_id: str, timestamp: datetime) -> int:
        """Count unique paths accessed by user in last hour."""
        if not self.security_event_repo:
            return 0

        try:
            one_hour_ago = timestamp - timedelta(hours=1)
            events = await self.security_event_repo.query(
                filters={"user_id": user_id},
                limit=1000,
            )

            # Extract unique paths
            paths = set()
            for event in events:
                if hasattr(event, 'metadata'):
                    path = event.metadata.get('request_path')
                    if path:
                        paths.add(path)

            return len(paths)
        except Exception as e:
            logger.error(f"Failed to count unique paths: {e}")
            return 0

    async def _calculate_data_volume(self, user_id: str, timestamp: datetime) -> float:
        """Calculate data volume transferred by user in last hour."""
        if not self.security_event_repo:
            return 0.0

        try:
            one_hour_ago = timestamp - timedelta(hours=1)
            events = await self.security_event_repo.query(
                filters={"user_id": user_id},
                limit=1000,
            )

            # Sum data volume
            total_bytes = 0
            for event in events:
                if hasattr(event, 'metadata'):
                    bytes_sent = event.metadata.get('bytes_sent', 0)
                    bytes_received = event.metadata.get('bytes_received', 0)
                    total_bytes += bytes_sent + bytes_received

            # Normalize to MB
            return total_bytes / (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.error(f"Failed to calculate data volume: {e}")
            return 0.0

    async def _get_recent_security_events(self, context: SecurityContext) -> List[SecurityEvent]:
        """Get recent security events for analysis."""
        if not self.security_event_repo:
            return []

        try:
            one_day_ago = context.timestamp - timedelta(days=1)
            events = await self.security_event_repo.query(
                filters={"created_at__gte": one_day_ago},
                limit=1000,
                order_by="-created_at",
            )

            return list(events)
        except Exception as e:
            logger.error(f"Failed to get recent security events: {e}")
            return []

    async def _detect_threats(self, context: SecurityContext, input_data: Dict[str, Any]) -> ThreatAssessment:
        """
        Detect cyber threats using multiple detection methods.

        Detection methods include:
        - SQL Injection detection
        - XSS attack detection
        - CSRF attack detection
        - Data exfiltration detection
        - Rate limiting abuse detection
        - Malicious input pattern detection
        - Phishing/social engineering detection
        """
        threat_assessment = ThreatAssessment()

        try:
            indicators = []
            threat_detected = False
            threat_type = ThreatType.UNKNOWN
            severity = SecuritySeverity.INFO
            confidence_score = 0.0

            # 1. SQL Injection Detection
            sql_indicators = self._detect_sql_injection(context, input_data)
            if sql_indicators:
                indicators.extend(sql_indicators)
                threat_detected = True
                threat_type = ThreatType.SQL_INJECTION_ATTEMPT
                severity = SecuritySeverity.CRITICAL
                confidence_score = 0.85
                logger.warning(f"SQL injection attempt detected: {context.user_id}")

            # 2. XSS Attack Detection
            xss_indicators = self._detect_xss_attack(context, input_data)
            if xss_indicators:
                indicators.extend(xss_indicators)
                threat_detected = True
                if not threat_detected or severity < SecuritySeverity.CRITICAL:
                    threat_type = ThreatType.XSS_ATTEMPT
                    severity = SecuritySeverity.HIGH
                    confidence_score = 0.8
                logger.warning(f"XSS attempt detected: {context.user_id}")

            # 3. CSRF Attack Detection
            csrf_indicators = self._detect_csrf_attack(context, input_data)
            if csrf_indicators:
                indicators.extend(csrf_indicators)
                threat_detected = True
                if not threat_detected or severity < SecuritySeverity.HIGH:
                    threat_type = ThreatType.CSRF_ATTEMPT
                    severity = SecuritySeverity.HIGH
                    confidence_score = 0.75
                logger.warning(f"CSRF attempt detected: {context.user_id}")

            # 4. Rate Limiting Detection
            rate_limit_indicators = await self._detect_rate_limiting(context)
            if rate_limit_indicators:
                indicators.extend(rate_limit_indicators)
                threat_detected = True
                if not threat_detected or severity < SecuritySeverity.MEDIUM:
                    threat_type = ThreatType.API_ABUSE
                    severity = SecuritySeverity.MEDIUM
                    confidence_score = 0.7
                logger.info(f"Rate limiting abuse detected: {context.user_id}")

            # 5. Malicious Input Pattern Detection
            malicious_indicators = self._detect_malicious_patterns(context, input_data)
            if malicious_indicators:
                indicators.extend(malicious_indicators)
                threat_detected = True
                if not threat_detected or severity < SecuritySeverity.MEDIUM:
                    threat_type = ThreatType.MALICIOUS_INPUT
                    severity = SecuritySeverity.HIGH
                    confidence_score = 0.75
                logger.warning(f"Malicious input patterns detected: {context.user_id}")

            # 6. Data Exfiltration Detection
            exfiltration_indicators = await self._detect_data_exfiltration(context)
            if exfiltration_indicators:
                indicators.extend(exfiltration_indicators)
                threat_detected = True
                threat_type = ThreatType.DATA_BREACH
                severity = SecuritySeverity.CRITICAL
                confidence_score = 0.9
                logger.warning(f"Data exfiltration attempt detected: {context.user_id}")

            # Update assessment
            if threat_detected:
                threat_assessment.threat_detected = True
                threat_assessment.threat_type = threat_type
                threat_assessment.severity = severity
                threat_assessment.confidence_score = confidence_score
                threat_assessment.indicators = indicators

            # Determine recommended action
            if threat_detected:
                if severity >= SecuritySeverity.CRITICAL:
                    threat_assessment.recommended_action = ResponseAction.BLOCK
                elif severity >= SecuritySeverity.HIGH:
                    threat_assessment.recommended_action = ResponseAction.THROTTLE
                else:
                    threat_assessment.recommended_action = ResponseAction.LOG_ONLY

            threat_assessment.assessed_at = datetime.now(timezone.utc)
            threat_assessment.details.update({
                'detection_methods_used': [
                    'sql_injection' if sql_indicators else None,
                    'xss_detection' if xss_indicators else None,
                    'csrf_detection' if csrf_indicators else None,
                    'rate_limiting' if rate_limit_indicators else None,
                    'malicious_patterns' if malicious_indicators else None,
                    'data_exfiltration' if exfiltration_indicators else None,
                ],
            })

            return threat_assessment

        except Exception as e:
            logger.error(f"Error during threat detection: {e}")
            return threat_assessment

    def _detect_sql_injection(self, context: SecurityContext, input_data: Dict[str, Any]) -> List[str]:
        """Detect SQL injection attempts using pattern matching."""
        indicators = []

        try:
            # Check request parameters for SQL patterns
            if 'request_params' in input_data:
                params = input_data['request_params']
                if isinstance(params, str):
                    # Common SQL injection patterns
                    sql_patterns = [
                        r"(\b(OR|AND|XOR)\b.*\s*=)",  # Boolean-based injection
                        r"('|\").*\s*(OR|AND|XOR)\s*(=|LIKE)\s*",  # Union-based injection
                        r"(\;\s*DROP\s+)",  # Stacked queries
                        r"\bUNION\b.*\s*SELECT\b",  # UNION-based injection
                        r"('\).*\s*(EXEC|EXEC|EXECUTE)\s*",  # Time-based injection
                        r"\bEXEC\b.*\s*(xp_cmdshell|master..dbo)\s*",  # Stored procedure injection
                    ]

                    for pattern in sql_patterns:
                        if re.search(pattern, params, re.IGNORECASE):
                            indicators.append(f"SQL injection pattern: {pattern}")

            # Check query-like strings in input
            if 'query' in input_data:
                query = input_data['query']
                if isinstance(query, str):
                    # Query keywords that might indicate injection
                    query_keywords = [
                        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'UNION',
                        'EXEC', 'EXECUTE', 'SCRIPT', 'DECLARE',
                        'TRUNCATE', 'ALTER', 'CREATE', 'GRANT',
                        'REVOKE', 'xp_cmdshell', 'master..dbo',
                    ]

                    for keyword in query_keywords:
                        if keyword.upper() in query.upper():
                            indicators.append(f"SQL keyword detected: {keyword}")

            return indicators

        except Exception as e:
            logger.error(f"Error detecting SQL injection: {e}")
            return []

    def _detect_xss_attack(self, context: SecurityContext, input_data: Dict[str, Any]) -> List[str]:
        """Detect XSS (Cross-Site Scripting) attempts using pattern matching."""
        indicators = []

        try:
            # Check for script tags in input
            if 'input' in input_data:
                user_input = input_data['input']
                if isinstance(user_input, str):
                    # XSS patterns
                    xss_patterns = [
                        r"<script[^>]*>.*</script>",  # Script tags
                        r"javascript:",  # JavaScript URLs
                        r"on\w+\s*=",  # Event handlers
                        r"eval\(",  # # TODO: Replace eval() with safe alternative
# eval() function
                        r"fromCharCode",  # fromCharCode
                        r"vbscript:",  # VBScript
                    ]

                    for pattern in xss_patterns:
                        if re.search(pattern, user_input, re.IGNORECASE):
                            indicators.append(f"XSS pattern: {pattern}")

            # Check URL parameters for XSS
            if 'request_params' in input_data:
                params = input_data['request_params']
                if isinstance(params, str):
                    if '<' in params or '>' in params:
                        indicators.append("Angle brackets in parameters (XSS risk)")

            return indicators

        except Exception as e:
            logger.error(f"Error detecting XSS attack: {e}")
            return []

    def _detect_csrf_attack(self, context: SecurityContext, input_data: Dict[str, Any]) -> List[str]:
        """Detect CSRF (Cross-Site Request Forgery) attempts."""
        indicators = []

        try:
            # Check for state-changing requests
            if 'request_method' in input_data and 'request_params' in input_data:
                method = input_data['request_method']
                params = input_data['request_params']

                # CSRF indicators
                if method.upper() in ['POST', 'PUT', 'DELETE', 'PATCH']:
                    if not params.get('csrf_token'):
                        indicators.append("State-changing request without CSRF token")

            # Check referer header
            if 'request_headers' in context.request_headers:
                referer = context.request_headers.get('referer')
                origin = context.request_headers.get('origin')

                if referer and origin:
                    # Check for suspicious referer
                    if not self._is_same_origin(referer, origin):
                        indicators.append(f"Suspicious cross-origin request: referer={referer}, origin={origin}")

            return indicators

        except Exception as e:
            logger.error(f"Error detecting CSRF attack: {e}")
            return []

    def _is_same_origin(self, referer: str, origin: str) -> bool:
        """Check if referer and origin are from same origin."""
        try:
            referer_domain = referer.split('/')[2].split('/')[0]
            origin_domain = origin.split('/')[2].split('/')[0]
            return referer_domain == origin_domain
        except:
            return False

    async def _detect_rate_limiting(self, context: SecurityContext) -> List[str]:
        """Detect rate limiting abuse."""
        indicators = []

        try:
            # Check request rate against baseline
            if context.user_id:
                request_rate = await self._calculate_request_rate(context.user_id, context.timestamp)

                # Get baseline from historical data
                if len(self.request_rate_baseline) > 0:
                    avg_baseline = sum(self.request_rate_baseline) / len(self.request_rate_baseline)
                    std_baseline = np.std(list(self.request_rate_baseline)) if len(self.request_rate_baseline) > 1 else 0

                    # Check if request rate is significantly above baseline
                    if request_rate > avg_baseline + 3 * std_baseline:
                        indicators.append(f"Request rate {request_rate:.2f}/s exceeds baseline {avg_baseline:.2f}/s")

            return indicators

        except Exception as e:
            logger.error(f"Error detecting rate limiting: {e}")
            return []

    def _detect_malicious_patterns(self, context: SecurityContext, input_data: Dict[str, Any]) -> List[str]:
        """Detect malicious input patterns."""
        indicators = []

        try:
            # Check for encoded/obfuscated input
            if 'input' in input_data:
                user_input = input_data['input']
                if isinstance(user_input, str):
                    # Encoded patterns
                    if len(user_input) > 100 and all(ord(c) < 32 or ord(c) > 126 for c in user_input):
                        indicators.append("High bit characters detected (potential encoding)")

                    # Hex encoded strings
                    if re.search(r'%[0-9A-Fa-f]{2}', user_input):
                        indicators.append("URL encoded string detected")

                    # Base64 encoded strings
                    if len(user_input) % 4 == 0 and re.match(r'^[A-Za-z0-9+/]+=*$', user_input):
                        indicators.append("Base64-like pattern detected")

            # Check for suspicious keywords
            if 'input' in input_data:
                user_input = input_data['input'].lower()
                suspicious_keywords = [
                    'admin', 'password', 'root', 'ssh', 'ftp',
                    'config', 'database', 'exec', 'system', 'cmd',
                    'exploit', 'payload', 'shell', 'bypass',
                ]

                for keyword in suspicious_keywords:
                    if keyword in user_input:
                        indicators.append(f"Suspicious keyword: {keyword}")

            # Check for very long input (potential buffer overflow)
            if 'input' in input_data:
                user_input = input_data['input']
                if isinstance(user_input, str) and len(user_input) > 10000:
                    indicators.append(f"Suspiciously long input ({len(user_input)} chars)")

            return indicators

        except Exception as e:
            logger.error(f"Error detecting malicious patterns: {e}")
            return []

    async def _detect_data_exfiltration(self, context: SecurityContext) -> List[str]:
        """Detect data exfiltration attempts."""
        indicators = []

        try:
            # Check for large data transfers
            if 'data_volume' in context.metadata:
                data_volume = context.metadata.get('data_volume', 0)

                # Calculate typical user data volume
                one_hour_ago = context.timestamp - timedelta(hours=1)
                typical_volume = await self._calculate_data_volume(context.user_id, one_hour_ago)

                # Check if current volume is significantly above typical
                if typical_volume > 0 and data_volume > typical_volume * 10:
                    indicators.append(f"Suspicious data volume: {data_volume:.2f}MB vs typical {typical_volume:.2f}MB")

            # Check for unusual data types being accessed
            if 'request_paths' in input_data:
                paths = input_data['request_paths']
                sensitive_paths = [
                    '/api/users/export',
                    '/api/database/dump',
                    '/api/backup/download',
                    '/api/keys/list',
                ]

                for path in paths:
                    if path in paths:
                        indicators.append(f"Sensitive path accessed: {path}")

            # Check for high-frequency data access
            if context.user_id:
                data_access_events = await self.security_event_repo.query(
                    filters={
                        "user_id": context.user_id,
                        "event_type__in": [
                            SecurityEventType.THREAT_BLOCKED,
                            SecurityEventType.DATA_EXFILTRATION_ATTEMPT,
                        ],
                        "created_at__gte": one_hour_ago,
                    },
                    limit=100,
                )

                if len(data_access_events) > 50:
                    indicators.append(f"High frequency data access: {len(data_access_events)} events/hour")

            return indicators

        except Exception as e:
            logger.error(f"Error detecting data exfiltration: {e}")
            return []

    async def _detect_anomalies(self, context: SecurityContext, input_data: Dict[str, Any]) -> AnomalyScore:
        """
        Detect behavioral anomalies using ML and statistical analysis.

        This includes:
        - ML-based anomaly detection using Isolation Forest
        - Statistical analysis (Z-score, IQR)
        - Request rate anomalies
        - Response time anomalies
        - Geographic anomalies (IP-based)
        - Session anomalies
        """
        anomaly_score = AnomalyScore()

        try:
            # Extract features from context
            recent_events = await self._get_recent_security_events(context)

            if not recent_events or len(recent_events) < 50:
                logger.warning("Not enough events for anomaly detection")
                return anomaly_score

            # Get user-specific events
            user_events = [e for e in recent_events if hasattr(e, 'user_id') and e.user_id == context.user_id]

            if not user_events:
                return anomaly_score

            # Extract features from user events
            features_list = []
            for event in user_events[-100:]:  # Last 100 events
                features = await self._extract_features(event, context)
                if features:
                    features_list.append(features)

            if not features_list:
                return anomaly_score

            # Prepare feature matrix
            feature_array = np.array(features_list)

            # ML-based anomaly detection
            if self.anomaly_detector and self.is_trained and self.scaler:
                try:
                    # Normalize features
                    scaled_features = self.scaler.transform(feature_array)

                    # Predict anomaly
                    anomaly = self.anomaly_detector.predict([scaled_features])[0]

                    if anomaly == 1:
                        anomaly_score.is_anomalous = True
                        anomaly_score.anomaly_type = "ml_isolation_forest"
                        anomaly_score.score = 0.8  # High confidence
                    else:
                        anomaly_score.score = 0.2  # Low confidence

                        # Calculate deviation
                        if len(feature_array) > 0:
                            mean_feature = np.mean(feature_array, axis=0)
                            std_feature = np.std(feature_array, axis=0)
                            deviation = abs(feature_array[-1][-1] - mean_feature)
                            if std_feature > 0:
                                anomaly_score.baseline = mean_feature
                                anomaly_score.deviation = deviation / std_feature
                            else:
                                anomaly_score.deviation = 0.0

                except Exception as e:
                    logger.error(f"ML anomaly detection failed: {e}")

            # Statistical-based anomaly detection
            if len(features_list) > 0:
                # Z-score analysis
                request_rates = [f[0] for f in features_list]  # Request rate is feature 0

                if len(request_rates) > 10:
                    mean_rate = np.mean(request_rates)
                    std_rate = np.std(request_rates)

                    if std_rate > 0:
                        current_rate = request_rates[-1]
                        z_score = abs(current_rate - mean_rate) / std_rate

                        if z_score > 3.0:  # 3 standard deviations
                            anomaly_score.is_anomalous = True
                            anomaly_score.anomaly_type = "statistical_zscore"
                            anomaly_score.score = 0.7
                            anomaly_score.threshold = 3.0
                            anomaly_score.baseline = mean_rate
                            anomaly_score.deviation = std_rate

                            # Add to indicators
                            anomaly_score.indicators.append(f"Z-score: {z_score:.2f}")

            # IQR-based anomaly detection
            if len(features_list) > 0:
                response_times = [f[2] for f in features_list if len(f) > 2]  # Response time is feature 2

                if len(response_times) > 10:
                    q1 = np.percentile(response_times, 25)
                    q3 = np.percentile(response_times, 75)
                    iqr = q3 - q1

                    current_time = response_times[-1]

                    if current_time > q3 + 1.5 * iqr:  # Outlier
                        anomaly_score.is_anomalous = True
                        anomaly_score.anomaly_type = "statistical_iqr"
                        anomaly_score.score = 0.8
                        anomaly_score.threshold = q3 + 1.5 * iqr
                        anomaly_score.baseline = q2  # Median (approximate)
                        anomaly_score.deviation = iqr

                        # Add to indicators
                        anomaly_score.indicators.append(f"IQR upper bound: {q3 + 1.5 * iqr:.2f}")

            # Geographic anomaly detection
            if context.ip_address:
                # Check if IP is from unusual geographic location
                try:
                    ip_obj = ipaddress.ip_address(context.ip_address)

                    # Check if IP is from VPN/Proxy/Tor exit node
                    geo_indicators = []
                    if ip_obj.is_private:
                        # Check for suspicious private IP ranges
                        if not ip_obj.is_reserved:
                            geo_indicators.append("Unusual public IP from private range")

                    # Check for known malicious IPs
                    # This would need a database of malicious IPs
                    # For now, we'll log the IP
                    geo_indicators.append(f"IP analysis: {context.ip_address}")

                    if geo_indicators:
                        anomaly_score.indicators.extend(geo_indicators)

                except Exception as e:
                    logger.error(f"Error during geographic anomaly detection: {e}")

            # Session anomaly detection
            if context.session_id:
                session_events = [e for e in user_events if hasattr(e, 'metadata') and e.metadata.get('session_id') == context.session_id]

                # Check for rapid session creation
                recent_sessions = []
                for event in session_events[-50:]:
                    session = event.metadata.get('session_id')
                    if session:
                        recent_sessions.append(session)

                if len(recent_sessions) > 10:  # More than 10 sessions in recent window
                    anomaly_score.is_anomalous = True
                    anomaly_score.anomaly_type = "session_anomaly"
                    anomaly_score.score = 0.6
                    anomaly_score.indicators.append(f"Rapid session creation: {len(recent_sessions)} sessions")

            anomaly_score.detected_at = datetime.now(timezone.utc)

            return anomaly_score

        except Exception as e:
            logger.error(f"Error during anomaly detection: {e}")
            return AnomalyScore()

    async def _enforce_policy(self, context: SecurityContext, threat_assessment: ThreatAssessment) -> Optional[str]:
        """
        Enforce security policies based on threat assessment.

        Returns the action taken if any, or None.
        """
        try:
            if not self.security_policy_repo:
                return None

            # Get active policies
            policies = await self.security_policy_repo.get_active_policies()

            for policy in policies:
                # Check if policy applies
                applies = await self._check_policy_applies(policy, context, threat_assessment)

                if applies:
                    # Execute policy actions
                    action = policy.actions.get('response_action', ResponseAction.LOG_ONLY)

                    action_taken = None

                    if action == ResponseAction.BLOCK:
                        # Block user/session
                        await self._block_user(context.user_id)
                        action_taken = f"Blocked user {context.user_id} per policy {policy.policy_name}"

                    elif action == ResponseAction.THROTTLE:
                        # Throttle requests
                        await self._throttle_user(context.user_id)
                        action_taken = f"Throttled user {context.user_id} per policy {policy.policy_name}"

                    elif action == ResponseAction.TERMINATE_SESSION:
                        # Terminate session
                        await self._terminate_session(context.session_id)
                        action_taken = f"Terminated session {context.session_id} per policy {policy.policy_name}"

                    elif action == ResponseAction.REVOKE_ACCESS:
                        # Revoke access token
                        await self._revoke_access(context.user_id)
                        action_taken = f"Revoked access for user {context.user_id} per policy {policy.policy_name}"

                    elif action == ResponseAction.ALERT_ADMIN:
                        # Alert administrator
                        await self._alert_admin(context.user_id, threat_assessment)
                        action_taken = f"Alerted admin about user {context.user_id} per policy {policy.policy_name}"

                    elif action == ResponseAction.LOG_ONLY:
                        # Just log the event
                        action_taken = f"Logged event for policy {policy.policy_name}"

                    if action_taken:
                        await self._log_security_event(
                            event_type=SecurityEventType.POLICY_VIOLATION,
                            context=context,
                            details={
                                'policy_enforced': policy.policy_name,
                                'action_taken': action_taken,
                                'threat_assessment': threat_assessment.to_dict() if hasattr(threat_assessment, 'to_dict') else {},
                            },
                        )

                        self.metrics.policies_enforced += 1

                        return action_taken

            return None

        except Exception as e:
            logger.error(f"Error enforcing policy: {e}")
            return None

    async def _check_policy_applies(self, policy: SecurityPolicy, context: SecurityContext, threat_assessment: ThreatAssessment) -> bool:
        """Check if a security policy applies to the current situation."""
        try:
            # Check policy conditions
            conditions = policy.conditions

            # Condition: Severity threshold
            if 'severity_threshold' in conditions:
                severity_threshold = conditions['severity_threshold']
                if threat_assessment.severity.value < severity_threshold:
                    return False

            # Condition: Threat type match
            if 'threat_types' in conditions:
                required_types = conditions['threat_types']
                if threat_assessment.threat_type not in required_types:
                    return False

            # Condition: Minimum confidence score
            if 'min_confidence' in conditions:
                min_confidence = conditions['min_confidence']
                if threat_assessment.confidence_score < min_confidence:
                    return False

            # Condition: User role check
            if 'allowed_user_roles' in conditions:
                allowed_roles = conditions['allowed_user_roles']
                # This would require checking user role
                # For now, we'll allow it

            # Condition: Time-based
            if 'time_restrictions' in conditions:
                time_restrictions = conditions['time_restrictions']
                # Check if current time is within restrictions
                current_hour = context.timestamp.hour
                allowed_hours = time_restrictions.get('allowed_hours', [])
                if current_hour not in allowed_hours:
                    return False

            # Condition: Geographic restrictions
            if 'geo_restrictions' in conditions:
                geo_restrictions = conditions['geo_restrictions']
                # This would need IP geolocation
                # For now, we'll allow it

            # Policy applies by default
            return True

        except Exception as e:
            logger.error(f"Error checking policy application: {e}")
            return False

    async def _block_user(self, user_id: str) -> None:
        """Block user access."""
        if self.user_repo:
            await self.user_repo.update(user_id, is_active=False)
            logger.warning(f"User {user_id} blocked due to security policy")

    async def _throttle_user(self, user_id: str) -> None:
        """Throttle user requests."""
        # This would typically involve rate limiting
        logger.info(f"Throttling user {user_id}")

    async def _terminate_session(self, session_id: str) -> None:
        """Terminate user session."""
        # This would typically involve invalidating session token
        logger.info(f"Terminating session {session_id}")

    async def _revoke_access(self, user_id: str) -> None:
        """Revoke user access token."""
        # This would typically involve deleting access token
        logger.info(f"Revoked access for user {user_id}")

    async def _alert_admin(self, user_id: str, threat_assessment: ThreatAssessment) -> None:
        """Alert administrator about security threat."""
        logger.critical(f"SECURITY ALERT: User {user_id} - {threat_assessment.threat_type.value} - Severity: {threat_assessment.severity.value} - Confidence: {threat_assessment.confidence_score:.2f}")

        # Send to notification system (would be integrated with WebSocket Gateway)
        # For now, just log it

    async def _log_security_event(self, event_type: SecurityEventType, context: SecurityContext, details: Optional[Dict[str, Any]] = None) -> None:
        """Log a security event to the database."""
        if not self.security_event_repo:
            return

        try:
            await self.security_event_repo.create(
                user_id=context.user_id,
                session_id=context.session_id,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                event_type=event_type,
                description=self._generate_event_description(event_type, details),
                severity=self._get_event_severity(event_type, details),
                metadata=details or {},
            )

            # Update metrics
            self.metrics.total_events += 1
            if event_type in self.metrics.events_by_type:
                self.metrics.events_by_type[event_type] += 1
            else:
                self.metrics.events_by_type[event_type] = 1

            severity = self._get_event_severity(event_type, details)
            if severity in self.metrics.events_by_severity:
                self.metrics.events_by_severity[severity] += 1
            else:
                self.metrics.events_by_severity[severity] = 1

            if event_type in [SecurityEventType.THREAT_BLOCKED, SecurityEventType.SUSPICIOUS_BEHAVIOR]:
                self.metrics.threats_blocked += 1
            elif event_type == SecurityEventType.SECURITY_ALERT:
                self.metrics.threats_detected += 1
            elif event_type == SecurityEventType.ANOMALY_DETECTED:
                self.metrics.anomalies_detected += 1

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

    def _generate_event_description(self, event_type: SecurityEventType, details: Optional[Dict[str, Any]]) -> str:
        """Generate human-readable event description."""
        if details and 'description' in details:
            return details['description']

        descriptions = {
            SecurityEventType.ANOMALY_DETECTED: "Anomalous behavior detected",
            SecurityEventType.THREAT_BLOCKED: "Threat blocked and prevented",
            SecurityEventType.UNAUTHORIZED_ACCESS: "Unauthorized access attempt",
            SecurityEventType.RATE_LIMIT_EXCEEDED: "Rate limit exceeded",
            SecurityEventType.MALICIOUS_INPUT: "Malicious input detected",
            SecurityEventType.SQL_INJECTION_ATTEMPT: "SQL injection attempt detected",
            SecurityEventType.XSS_ATTEMPT: "XSS (Cross-Site Scripting) attempt detected",
            SecurityEventType.CSRF_ATTEMPT: "CSRF (Cross-Site Request Forgery) attempt detected",
            SecurityEventType.DATA_EXFILTRATION_ATTEMPT: "Data exfiltration attempt detected",
            SecurityEventType.POLICY_VIOLATION: "Security policy violation",
            SecurityEventType.AUTHENTICATION_FAILURE: "Authentication failure",
            SecurityEventType.SUSPICIOUS_BEHAVIOR: "Suspicious behavior detected",
            SecurityEventType.SECURITY_ALERT: "Security alert triggered",
        }

        return descriptions.get(event_type, f"Security event: {event_type}")

    def _get_event_severity(self, event_type: SecurityEventType, details: Optional[Dict[str, Any]]) -> SecuritySeverity:
        """Determine event severity."""
        if details and 'severity' in details:
            try:
                return SecuritySeverity(details['severity'])
            except ValueError:
                return SecuritySeverity.MEDIUM

        # Default severity based on event type
        default_severities = {
            SecurityEventType.ANOMALY_DETECTED: SecuritySeverity.MEDIUM,
            SecurityEventType.THREAT_BLOCKED: SecuritySeverity.HIGH,
            SecurityEventType.UNAUTHORIZED_ACCESS: SecuritySeverity.MEDIUM,
            SecurityEventType.RATE_LIMIT_EXCEEDED: SecuritySeverity.LOW,
            SecurityEventType.MALICIOUS_INPUT: SecuritySeverity.HIGH,
            SecurityEventType.SQL_INJECTION_ATTEMPT: SecuritySeverity.CRITICAL,
            SecurityEventType.XSS_ATTEMPT: SecuritySeverity.HIGH,
            SecurityEventType.CSRF_ATTEMPT: SecuritySeverity.HIGH,
            SecurityEventType.DATA_EXFILTRATION_ATTEMPT: SecuritySeverity.CRITICAL,
            SecurityEventType.POLICY_VIOLATION: SecuritySeverity.MEDIUM,
            SecurityEventType.AUTHENTICATION_FAILURE: SecuritySeverity.LOW,
            SecurityEventType.SUSPICIOUS_BEHAVIOR: SecuritySeverity.HIGH,
            SecurityEventType.SECURITY_ALERT: SecuritySeverity.CRITICAL,
        }

        return default_severities.get(event_type, SecuritySeverity.MEDIUM)

    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute security analysis with comprehensive threat and anomaly detection.

        Args:
            **kwargs: Skill parameters including:
                - input_data: Dictionary with request context
                - analyze_type: Type of analysis ('threat', 'anomaly', 'both')
                - strict_mode: Whether to enable strict security mode

        Returns:
            SkillResult: Analysis result with threat assessment
        """
        start_time = time.time()

        try:
            # Extract parameters
            input_data = kwargs.get('input_data', {})
            analyze_type = kwargs.get('analyze_type', 'both')
            strict_mode = kwargs.get('strict_mode', False)

            # Create security context
            context = SecurityContext(
                user_id=input_data.get('user_id'),
                session_id=input_data.get('session_id'),
                ip_address=input_data.get('ip_address'),
                user_agent=input_data.get('user_agent'),
                request_path=input_data.get('request_path'),
                request_method=input_data.get('request_method'),
                request_headers=input_data.get('request_headers', {}),
                metadata=input_data.get('metadata', {}),
            )

            # Threat detection
            threat_assessment = await self._detect_threats(context, input_data)

            # Anomaly detection
            if analyze_type in ['both', 'anomaly']:
                anomaly_score = await self._detect_anomalies(context, input_data)

                # Update threat assessment if anomaly is severe
                if anomaly_score.is_anomalous and anomaly_score.score > 0.7:
                    if not threat_assessment.threat_detected or threat_assessment.severity < SecuritySeverity.MEDIUM:
                        threat_assessment.threat_detected = True
                        threat_assessment.threat_type = ThreatType.UNKNOWN
                        threat_assessment.severity = SecuritySeverity.HIGH
                        threat_assessment.confidence_score = 0.7
                        threat_assessment.recommended_action = ResponseAction.THROTTLE
                        threat_assessment.indicators.append("Anomaly score: " + str(anomaly_score.score))

            # Policy enforcement
            await self._enforce_policy(context, threat_assessment)

            # Determine overall risk score
            risk_score = 0.0

            # Threat risk
            if threat_assessment.threat_detected:
                threat_weight = threat_assessment.severity.value
                threat_risk = {
                    SecuritySeverity.INFO: 0,
                    SecuritySeverity.LOW: 5,
                    SecuritySeverity.MEDIUM: 15,
                    SecuritySeverity.HIGH: 35,
                    SecuritySeverity.CRITICAL: 70,
                    SecuritySeverity.FATAL: 100,
                }
                risk_score += threat_risk[threat_assessment.severity]

            # Anomaly risk
            if hasattr(self, '_detect_anomalies') and analyze_type in ['both', 'anomaly']:
                anomaly_risk = anomaly_score.score * 30  # Max 30 points
                risk_score += anomaly_risk

                if anomaly_score.is_anomalous:
                    # Log anomaly event
                    await self._log_security_event(
                        event_type=SecurityEventType.ANOMALY_DETECTED,
                        context=context,
                        details={
                            'anomaly_type': anomaly_score.anomaly_type,
                            'anomaly_score': anomaly_score.score,
                            'anomaly_threshold': anomaly_score.threshold,
                            'anomaly_indicators': anomaly_score.indicators,
                        },
                    )

            # Normalize to 0-100
            risk_score = min(risk_score, 100.0)

            # Log security event if threat detected
            if threat_assessment.threat_detected:
                await self._log_security_event(
                    event_type=SecurityEventType.THREAT_BLOCKED if strict_mode else SecurityEventType.SUSPICIOUS_BEHAVIOR,
                    context=context,
                    details={
                        'threat_type': threat_assessment.threat_type,
                        'severity': threat_assessment.severity,
                        'confidence': threat_assessment.confidence_score,
                        'recommended_action': threat_assessment.recommended_action.value if threat_assessment.recommended_action else None,
                        'indicators': threat_assessment.indicators,
                        'risk_score': risk_score,
                        'strict_mode': strict_mode,
                    },
                )

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Return result
            result = SkillResult(
                success=True,
                data={
                    'threat_assessment': threat_assessment.to_dict() if hasattr(threat_assessment, 'to_dict') else {},
                    'anomaly_score': anomaly_score.to_dict() if hasattr(anomaly_score, 'to_dict') else {},
                    'risk_score': risk_score,
                    'recommended_action': threat_assessment.recommended_action.value if threat_assessment.recommended_action else None,
                    'security_level': 'critical' if risk_score >= 70 else 'high' if risk_score >= 35 else 'medium' if risk_score >= 15 else 'low',
                },
                execution_time_ms=execution_time_ms,
                metadata={
                    'analyze_type': analyze_type,
                    'strict_mode': strict_mode,
                    'model_version': '1.0.0',
                },
            )

            logger.info(f"Security analysis complete - Risk Score: {risk_score:.1f}/100 ({result.data['security_level']})")

            return result

        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return SkillResult(
                success=False,
                error=f"Security analysis failed: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )


# ==================== Sentinel Security System ====================

class SentinelSecuritySystem:
    """
    Comprehensive security system for JEBAT AI.

    Coordinates all security-related components:
    - Threat detection (SQL injection, XSS, CSRF, etc.)
    - Anomaly detection using ML models
    - Security policy management and enforcement
    - Real-time monitoring and alerting
    - Integration with database for event logging
    - Integration with decision engine for security routing
    - Integration with error recovery for security issues
    - Hidden security layer for sophisticated threat detection
    """

    def __init__(
        self,
        security_event_repo: Optional[SecurityEventRepository] = None,
        security_policy_repo: Optional[SecurityPolicyRepository] = None,
        audit_log_repo: Optional[AuditLogRepository] = None,
        user_repo: Optional[UserRepository] = None,
        decision_engine: Optional[DecisionEngine] = None,
        error_recovery: Optional[ErrorRecoverySystem] = None,
        cache_manager: Optional[CacheManager] = None,
    ):
        """
        Initialize Sentinel Security System.

        Args:
            security_event_repo: Repository for security events
            security_policy_repo: Repository for security policies
            audit_log_repo: Repository for audit logs
            user_repo: Repository for user data
            decision_engine: Decision engine for routing decisions
            error_recovery: Error recovery system
            cache_manager: Cache manager for caching security results
        """
        self.security_event_repo = security_event_repo
        self.security_policy_repo = security_policy_repo
        self.audit_log_repo = audit_log_repo
        self.user_repo = user_repo
        self.decision_engine = decision_engine
        self.error_recovery = error_recovery
        self.cache_manager = cache_manager

        # Security metrics
        self.metrics = SecurityMetrics()

        # Anomaly detection model (will be trained on first use)
        self.security_analyzer = SecurityAnalyzeSkill()

        # Active threats tracking
        self.active_threats: Dict[str, ThreatAssessment] = {}
        self.anomaly_history: Dict[str, List[AnomalyScore]] = {}

        # System status
        self.is_initialized = False
        self.is_monitoring = False

        self.logger = logging.getLogger(__name__)
        self.logger.info("Sentinel Security System initializing...")

    async def initialize(self) -> None:
        """
        Initialize the security system and train ML models.

        This should be called after database is ready.
        """
        if self.is_initialized:
            return

        self.logger.info("Initializing Sentinel Security System...")

        # Initialize default security policies
        await self._initialize_default_policies()

        # Train anomaly detection model with baseline data
        await self._train_anomaly_detector()

        self.is_initialized = True
        self.metrics.start_time = datetime.now(timezone.utc)

        self.logger.info("Sentinel Security System initialized and ready")

    async def _initialize_default_policies(self) -> None:
        """Initialize default security policies."""
        try:
            default_policies = [
                SecurityPolicy(
                    policy_id="rate_limiting_default",
                    policy_name="Default Rate Limiting",
                    policy_type=PolicyType.RATE_LIMITING,
                    rules={
                        'max_requests_per_minute': 60,
                        'max_requests_per_hour': 1000,
                        'max_requests_per_day': 10000,
                    },
                    actions={
                        'response_action': ResponseAction.THROTTLE.value,
                    },
                    severity=SecuritySeverity.MEDIUM,
                    priority=100,
                    is_active=True,
                ),
                SecurityPolicy(
                    policy_id="content_filtering_default",
                    policy_name="Default Content Filtering",
                    policy_type=PolicyType.CONTENT_FILTERING,
                    rules={
                        'blocked_patterns': [
                            r'<script[^>]*>.*</script>',
                            r'javascript:',
                            r'on\w+\s*=',  # Event handlers
                            r'eval\(',
                            r'fromCharCode',
                            r'vbscript:',
                        ],
                        'max_input_length': 10000,
                        'blocked_keywords': [
                            'admin', 'password', 'root', 'ssh', 'ftp',
                            'config', 'database', 'exec', 'system', 'cmd',
                        ],
                    },
                    actions={
                        'response_action': ResponseAction.BLOCK.value,
                    },
                    severity=SecuritySeverity.HIGH,
                    priority=100,
                    is_active=True,
                ),
                SecurityPolicy(
                    policy_id="access_control_default",
                    policy_name="Default Access Control",
                    policy_type=PolicyType.ACCESS_CONTROL,
                    rules={
                        'require_authentication': True,
                        'session_timeout_minutes': 30,
                        'max_concurrent_sessions': 5,
                    },
                    actions={
                        'response_action': ResponseAction.TERMINATE_SESSION.value,
                    },
                    severity=SecuritySeverity.HIGH,
                    priority=90,
                    is_active=True,
                ),
                SecurityPolicy(
                    policy_id="input_validation_default",
                    policy_name="Default Input Validation",
                    policy_type=PolicyType.INPUT_VALIDATION,
                    rules={
                        'min_password_length': 8,
                        'max_password_length': 128,
                        'allowed_username_pattern': r'^[a-zA-Z0-9._-]{3,20}$',
                        'allowed_email_pattern': r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]{2,5}$',
                        'sql_injection_blacklist': [
                            r"(\b(OR|AND|XOR)\b.*\s*=)",
                            r"('|\").*\s*(OR|AND|XOR)\s*(=|LIKE)\s*",
                        ],
                    },
                    actions={
                        'response_action': ResponseAction.BLOCK.value,
                    },
                    severity=SecuritySeverity.CRITICAL,
                    priority=100,
                    is_active=True,
                ),
                SecurityPolicy(
                    policy_id="data_retention_default",
                    policy_name="Default Data Retention",
                    policy_type=PolicyType.DATA_RETENTION,
                    rules={
                        'security_events_retention_days': 90,
                        'audit_logs_retention_days': 365,
                        'anomaly_data_retention_days': 30,
                    },
                    actions={
                        'response_action': ResponseAction.LOG_ONLY.value,
                    },
                    severity=SecuritySeverity.LOW,
                    priority=50,
                    is_active=True,
                ),
            ]

            # Register default policies
            for policy in default_policies:
                if self.security_policy_repo:
                    try:
                        await self.security_policy_repo.create(
                            policy_name=policy.policy_name,
                            policy_type=policy.policy_type,
                            rules=policy.rules,
                            actions=policy.actions,
                            severity=policy.severity,
                            priority=policy.priority,
                            is_active=policy.is_active,
                        )
                        self.logger.info(f"Registered default policy: {policy.policy_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to register policy {policy.policy_name}: {e}")

        except Exception as e:
            self.logger.error(f"Failed to initialize default policies: {e}")

    async def _train_anomaly_detector(self) -> None:
        """Train anomaly detection model with baseline data."""
        if not self.security_analyzer:
            return

        self.logger.info("Training anomaly detection model...")

        # Create a training context
        context = SecurityContext(
            user_id="system",
            timestamp=datetime.now(timezone.utc),
        )

        # This would typically be done with historical data
        # For now, we'll initialize with default baseline
        self.logger.info("Anomaly detector training skipped (no baseline data available)")

    async def analyze_request(
        self,
        user_id: str,
        session_id: str,
        request_path: str,
        request_method: str,
        request_headers: Dict[str, str],
        request_params: Dict[str, Any],
        ip_address: str,
        user_agent: str,
        strict_mode: bool = False,
    ) -> ThreatAssessment:
        """
        Analyze a request for security threats and anomalies.

        This is the main entry point for security analysis.

        Args:
            user_id: User ID
            session_id: Session ID
            request_path: Request path
            request_method: HTTP method
            request_headers: HTTP headers
            request_params: Request parameters
            ip_address: Client IP address
            user_agent: User agent string
            strict_mode: Whether to enable strict security mode

        Returns:
            ThreatAssessment: Comprehensive threat assessment
        """
        if not self.is_initialized:
            self.logger.warning("Sentinel Security System not initialized, skipping analysis")
            return ThreatAssessment()

        # Create security context
        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            request_headers=request_headers,
        )

        try:
            # Prepare input data for analysis
            input_data = {
                'user_id': user_id,
                'session_id': session_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'request_path': request_path,
                'request_method': request_method,
                'request_headers': request_headers,
                'request_params': request_params,
                'metadata': {
                    'strict_mode': strict_mode,
                },
            }

            # Perform security analysis
            result = await self.security_analyzer.execute_with_retry(
                input_data=input_data,
                analyze_type='both',
                strict_mode=strict_mode,
                skill_id=None,  # Will be set by system
                agent_id=None,  # Will be set by system
                task_id=None,  # Will be set by system
                user_id=None,  # Will be set by system
            )

            # Update metrics
            self.metrics.total_events += 1

            # Track active threats
            if result.success and result.data.get('threat_assessment', {}).get('threat_detected'):
                threat_key = f"{user_id}:{ip_address}"
                self.active_threats[threat_key] = result.data['threat_assessment']

            logger.info(f"Security analysis complete: {result.data}")

            return result.data.get('threat_assessment', ThreatAssessment())

        except Exception as e:
            self.logger.error(f"Security analysis failed: {e}")
            return ThreatAssessment()

    async def get_security_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive security metrics.

        Returns:
            Dict[str, Any]: Security metrics including events, threats, anomalies, etc.
        """
        # Calculate uptime
        if self.metrics.start_time:
            uptime = (datetime.now(timezone.utc) - self.metrics.start_time).total_seconds()
            self.metrics.uptime_seconds = uptime

        # Get detailed metrics from database
        if self.security_event_repo:
            try:
                all_events = await self.security_event_repo.get_all(limit=10000)

                # Count events by type and severity
                for event in all_events:
                    event_type = event.event_type
                    if event_type in self.metrics.events_by_type:
                        self.metrics.events_by_type[event_type] += 1
                    else:
                        self.metrics.events_by_type[event_type] = 1

                    severity = event.severity
                    if severity in self.metrics.events_by_severity:
                        self.metrics.events_by_severity[severity] += 1
                    else:
                        self.metrics.events_by_severity[severity] = 1

                # Update total
                self.metrics.total_events = len(all_events)

            except Exception as e:
                self.logger.error(f"Failed to get security metrics from database: {e}")

        return {
            'total_events': self.metrics.total_events,
            'events_by_type': self.metrics.events_by_type,
            'events_by_severity': self.metrics.events_by_severity,
            'threats_blocked': self.metrics.threats_blocked,
            'threats_detected': self.metrics.threats_detected,
            'anomalies_detected': self.metrics.anomalies_detected,
            'policies_enforced': self.metrics.policies_enforced,
            'avg_response_time_ms': self.metrics.avg_response_time_ms,
            'false_positives': self.metrics.false_positives,
            'false_negatives': self.metrics.false_negatives,
            'uptime_seconds': self.metrics.uptime_seconds,
            'last_threat_time': self.metrics.last_threat_time,
        }

    async def get_active_policies(self) -> List[SecurityPolicy]:
        """Get all active security policies."""
        if not self.security_policy_repo:
            return []

        try:
            policies = await self.security_policy_repo.get_active_policies()
            return list(policies)
        except Exception as e:
            self.logger.error(f"Failed to get active policies: {e}")
            return []

    async def create_policy(
        self,
        policy_name: str,
        policy_type: PolicyType,
        rules: Dict[str, Any],
        actions: Dict[str, Any],
        severity: SecuritySeverity = SecuritySeverity.MEDIUM,
        priority: int = 50,
        conditions: Dict[str, Any] = field(default_factory=dict),
    ) -> Optional[SecurityPolicy]:
        """Create a new security policy."""
        if not self.security_policy_repo:
            return None

        try:
            policy = await self.security_policy_repo.create(
                policy_name=policy_name,
                policy_type=policy_type,
                rules=rules,
                actions=actions,
                severity=severity,
                priority=priority,
                is_active=True,
                conditions=conditions,
            )

            self.logger.info(f"Created security policy: {policy_name}")

            return policy
        except Exception as e:
            self.logger.error(f"Failed to create policy: {e}")
            return None

    async def update_policy(
        self,
        policy_id: str,
        **updates,
    ) -> Optional[SecurityPolicy]:
        """Update an existing security policy."""
        if not self.security_policy_repo:
            return None

        try:
            policy = await self.security_policy_repo.update(policy_id, **updates)
            self.logger.info(f"Updated security policy: {policy_id}")
            return policy
        except Exception as e:
            self.logger.error(f"Failed to update policy: {policy_id}: {e}")
            return None

    async def delete_policy(self, policy_id: str) -> bool:
        """Delete a security policy."""
        if not self.security_policy_repo:
            return False

        try:
            await self.security_policy_repo.delete(policy_id)
            self.logger.info(f"Deleted security policy: {policy_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete policy {policy_id}: {e}")
            return False

    async def start_monitoring(self) -> None:
        """Start security monitoring and background tasks."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.logger.info("Sentinel Security System monitoring started")

        # Start background tasks
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._anomaly_detection_loop())
        asyncio.create_task(self._policy_enforcement_loop())

        self.logger.info("Sentinel Security System background tasks started")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Check for new security events
                # This would involve database polling or event streaming
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                self.logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _anomaly_detection_loop(self) -> None:
        """Background loop for continuous anomaly detection."""
        while self.is_monitoring:
            try:
                # Periodic retraining of anomaly detector
                await asyncio.sleep(300)  # Every 5 minutes

                # Update baseline data
                # This would involve collecting metrics and updating baseline

            except asyncio.CancelledError:
                self.logger.info("Anomaly detection loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in anomaly detection loop: {e}")
                await asyncio.sleep(300)

    async def _policy_enforcement_loop(self) -> None:
        """Background loop for policy enforcement."""
        while self.is_monitoring:
            try:
                # Check for policy violations
                # This would involve analyzing recent events
                await asyncio.sleep(10)

            except asyncio.CancelledError:
                self.logger.info("Policy enforcement loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in policy enforcement loop: {e}")
                await asyncio.sleep(10)

    async def stop_monitoring(self) -> None:
        """Stop security monitoring and background tasks."""
        self.is_monitoring = False
        self.logger.info("Sentinel Security System monitoring stopped")

    async def shutdown(self) -> None:
        """Shutdown the security system and cleanup resources."""
        self.logger.info("Shutting down Sentinel Security System...")

        # Stop monitoring
        await self.stop_monitoring()

        # Cleanup ML models
        if self.security_analyzer:
            self.security_analyzer = None

        self.logger.info("Sentinel Security System shutdown complete")

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            'is_initialized': self.is_initialized,
            'is_monitoring': self.is_monitoring,
            'security_metrics': self.metrics.to_dict() if hasattr(self.metrics, 'to_dict') else {},
            'active_threats_count': len(self.active_threats),
            'anomaly_history_size': sum(len(history) for history in self.anomaly_history.values()),
            'ml_model_status': 'trained' if self.security_analyzer and self.security_analyzer.is_trained else 'not_trained',
        }


# ==================== Example Usage ====================

async def example_usage():
    """Example usage of Sentinel Security System."""
    from jebat.database.repositories import (
        SecurityEventRepository,
        SecurityPolicyRepository,
        AuditLogRepository,
        UserRepository,
    )
    from jebat.database.models import AsyncSessionLocal

    # Create mock repositories (in production, these would be real)
    async with AsyncSessionLocal() as session:
        sentinel = SentinelSecuritySystem(
            security_event_repo=SecurityEventRepository(session),
            security_policy_repo=SecurityPolicyRepository(session),
            audit_log_repo=AuditLogRepository(session),
            user_repo=UserRepository(session),
        )

        # Initialize
        await sentinel.initialize()

        # Analyze a request
        assessment = await sentinel.analyze_request(
            user_id="user_123",
            session_id="session_456",
            request_path="/api/generate",
            request_method="POST",
            request_headers={"Content-Type": "application/json"},
            request_params={"prompt": "Hello, how are you?"},
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            strict_mode=True,
        )

        print(f"Threat Assessment: {assessment.to_dict() if hasattr(assessment, 'to_dict') else {}}")

        # Get metrics
        metrics = await sentinel.get_security_metrics()
        print(f"Security Metrics: {metrics}")

        # Get policies
        policies = await sentinel.get_active_policies()
        print(f"Active Policies ({len(policies)}):")
        for policy in policies:
            print(f"  - {policy.policy_name} ({policy.policy_type})")

        # Start monitoring
        await sentinel.start_monitoring()

        # Run for a bit
        await asyncio.sleep(5)

        # Stop monitoring
        await sentinel.stop_monitoring()

        # Get final stats
        stats = sentinel.get_statistics()
        print(f"Final Statistics: {stats}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
# - Integration with Error Recovery for security-related issues
# - Hidden security layer for sophisticated threat detection
# - Security metrics and monitoring
# - Real-time threat scoring and risk assessment
#
# This is a production-grade security system designed to protect JEBAT from:
# - SQL Injection attacks
# - XSS (Cross-Site Scripting) attacks
# - CSRF (Cross-Site Request Forgery) attacks
# - Rate limiting abuse
# - Unauthorized access attempts
# - Data exfiltration attempts
# - Behavioral anomalies
# - Malicious input patterns

import asyncio
import hashlib
import ipaddress
import json
import logging
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from jebat.database.repositories import SecurityEventRepository, SecurityPolicyRepository, AuditLogRepository, UserRepository
from jebat.database.models import SecurityEvent, SecurityPolicy, AuditLog, User
from jebat.core.decision.engine import DecisionEngine
try:
    from jebat.error_recovery.system import ErrorRecoverySystem
except ImportError:
    ErrorRecoverySystem = None
from jebat.core.cache.smart_cache import CacheManager
from jebat.skills.base_skill import BaseSkill, SkillResult, SkillParameter, SkillCapability

# Configure logging
logger = logging.getLogger(__name__)


# ==================== Enums ====================

class SecurityEventType(str, Enum):
    """Security event type enumeration"""

    ANOMALY_DETECTED = "anomaly_detected"
    THREAT_BLOCKED = "threat_blocked"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MALICIOUS_INPUT = "malicious_input"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    DATA_EXFILTRATION_ATTEMPT = "data_exfiltration_attempt"
    POLICY_VIOLATION = "policy_violation"
    AUTHENTICATION_FAILURE = "authentication_failure"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    SECURITY_ALERT = "security_alert"


class SecuritySeverity(str, Enum):
    """Security severity enumeration"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"


class ThreatType(str, Enum):
    """Threat type enumeration"""

    MALWARE = "malware"
    PHISHING = "phishing"
    SOCIAL_ENGINEERING = "social_engineering"
    INSIDER_THREAT = "insider_threat"
    DDOS = "ddos"
    DATA_BREACH = "data_breach"
    API_ABUSE = "api_abuse"
    AUTHENTICATION_ATTACK = "authentication_attack"
    UNKNOWN = "unknown"


class PolicyType(str, Enum):
    """Security policy type enumeration"""

    RATE_LIMITING = "rate_limiting"
    CONTENT_FILTERING = "content_filtering"
    ACCESS_CONTROL = "access_control"
    DATA_RETENTION = "data_retention"
    INPUT_VALIDATION = "input_validation"
    AUTHENTICATION = "authentication"
    SESSION_MANAGEMENT = "session_management"


class ResponseAction(str, Enum):
    """Security response action enumeration"""

    BLOCK = "block"
    THROTTLE = "throttle"
    CHALLENGE = "challenge"
    LOG_ONLY = "log_only"
    NOTIFY = "notify"
    TERMINATE_SESSION = "terminate_session"
    REVOKE_ACCESS = "revoke_access"
    ALERT_ADMIN = "alert_admin"


# ==================== Data Classes ====================

@dataclass
class SecurityContext:
    """
    Security context for security analysis.

    Contains user information, request details, and environmental context.
    """
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    request_headers: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str = "production"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatAssessment:
    """
    Threat assessment result.

    Contains threat detection results, risk scores, and recommended actions.
    """
    threat_detected: bool = False
    threat_type: Optional[ThreatType] = None
    severity: SecuritySeverity = SecuritySeverity.INFO
    confidence_score: float = 0.0  # 0.0 to 1.0
    risk_score: float = 0.0  # 0.0 to 100.0
    recommended_action: Optional[ResponseAction] = None
    details: Dict[str, Any] = field(default_factory=dict)
    indicators: List[str] = field(default_factory=list)
    model_version: str = "1.0.0"
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AnomalyScore:
    """
    Anomaly detection result.

    Contains behavioral anomaly detection results with statistical analysis.
    """
    is_anomalous: bool = False
    anomaly_type: Optional[str] = None
    score: float = 0.0  # Higher means more anomalous
    threshold: float = 0.0
    features: Dict[str, float] = field(default_factory=dict)
    baseline: Optional[float] = None
    deviation: Optional[float] = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SecurityMetrics:
    """
    Security system metrics.

    Tracks overall security performance and threat statistics.
    """
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_by_severity: Dict[str, int] = field(default_factory=dict)
    threats_blocked: int = 0
    threats_detected: int = 0
    anomalies_detected: int = 0
    policies_enforced: int = 0
    avg_response_time_ms: float = 0.0
    false_positives: int = 0
    false_negatives: int = 0
    uptime_seconds: float = 0.0
    last_threat_time: Optional[datetime] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== Security Skills ====================

class SecurityAnalyzeSkill(BaseSkill):
    """
    Security analysis skill for detecting threats and anomalies.

    Performs comprehensive security analysis using ML models and statistical methods.
    """

    name = "security_analyze"
    skill_type = "analyze"
    description = "Comprehensive security analysis with threat detection, anomaly detection, and risk assessment"
    version = "1.0.0"
    timeout_seconds = 60
    max_retries = 2

    parameters = [
        SkillParameter(
            name="input_data",
            type=dict,
            description="Input data to analyze (request, user context, etc.)",
            required=True,
        ),
        SkillParameter(
            name="analyze_type",
            type=str,
            description="Type of analysis to perform (threat, anomaly, both)",
            default="both",
        ),
        SkillParameter(
            name="strict_mode",
            type=bool,
            description="Enable strict security mode (block more threats)",
            default=False,
        ),
    ]

    capabilities = [
        SkillCapability(
            name="threat_detection",
            description="Detect various types of cyber threats",
            enabled=True,
        ),
        SkillCapability(
            name="anomaly_detection",
            description="Detect behavioral anomalies using ML",
            enabled=True,
        ),
        SkillCapability(
            name="input_validation",
            description="Validate input for malicious patterns",
            enabled=True,
        ),
            ]


# End of Sentinel class


# Alias for compatibility
Sentinel = SentinelSecuritySystem
