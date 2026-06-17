"""
JEBAT Encryption Module — Data-at-rest encryption for sensitive fields.

Provides:
- Fernet symmetric encryption for API keys, tokens, passwords
- Argon2id password hashing for user authentication
- Field-level encryption for database models
- Secure key derivation and rotation
"""

from __future__ import annotations

import base64
import os
import secrets
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


class EncryptionManager:
    """
    Manages encryption keys and operations for JEBAT.

    Keys are stored in ~/.jebat/secrets/encryption.key (auto-generated on first run)
    Master key is derived from environment variable or key file.
    """

    _instance: Optional["EncryptionManager"] = None

    def __new__(cls, key_path: Optional[Path] = None) -> "EncryptionManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, key_path: Optional[Path] = None):
        if getattr(self, '_initialized', False):
            return  # Already initialized

        if key_path is None:
            key_path = Path.home() / ".jebat" / "secrets" / "encryption.key"

        self._key_path = Path(key_path)
        self._fernet: Optional[Fernet] = None
        self._master_key: Optional[bytes] = None
        self._initialize()
        self._initialized = True

    def _initialize(self) -> None:
        """Load or generate encryption key."""
        self._master_key = self._load_or_generate_key()
        self._fernet = Fernet(self._master_key)

    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one."""
        if self._key_path.exists():
            try:
                with open(self._key_path, "rb") as f:
                    key = f.read().strip()
                    # Validate it's a valid Fernet key
                    Fernet(key)
                    return key
            except Exception:
                pass  # Fall through to generate new

        # Generate new key
        self._key_path.parent.mkdir(parents=True, exist_ok=True)
        key = Fernet.generate_key()
        with open(self._key_path, "wb") as f:
            f.write(key)
        # Restrict permissions
        os.chmod(self._key_path, 0o600)
        return key

    @property
    def fernet(self) -> Fernet:
        if self._fernet is None:
            self._initialize()
        return self._fernet

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        if not data:
            return ""
        token = self.fernet.encrypt(data.encode("utf-8"))
        return base64.urlsafe_b64encode(token).decode("ascii")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a base64-encoded ciphertext back to string."""
        if not encrypted_data:
            return ""
        try:
            token = base64.urlsafe_b64decode(encrypted_data.encode("ascii"))
            return self.fernet.decrypt(token).decode("utf-8")
        except Exception:
            # Return empty string on decryption failure (tamper detection)
            return ""

    def rotate_key(self) -> None:
        """Generate new encryption key (re-encrypt all data required)."""
        old_key = self._master_key
        self._master_key = Fernet.generate_key()
        self._fernet = Fernet(self._master_key)
        with open(self._key_path, "wb") as f:
            f.write(self._master_key)
        os.chmod(self._key_path, 0o600)
        # Note: Existing encrypted data must be re-encrypted with new key


class PasswordHasher:
    """
    Secure password hashing using Argon2id (memory-hard, resistant to GPU attacks).

    Configurable for different security/performance tradeoffs.
    """

    # Default parameters (balanced for security and performance)
    DEFAULT_HASH_LEN = 32
    DEFAULT_ITERATIONS = 3
    DEFAULT_LANES = 4
    DEFAULT_MEMORY_COST = 65536  # 64 MB

    def __init__(
        self,
        hash_len: int = DEFAULT_HASH_LEN,
        iterations: int = DEFAULT_ITERATIONS,
        lanes: int = DEFAULT_LANES,
        memory_cost: int = DEFAULT_MEMORY_COST,
    ):
        self.hash_len = hash_len
        self.iterations = iterations
        self.lanes = lanes
        self.memory_cost = memory_cost

    def hash(self, password: str) -> str:
        """Hash a password and return PHC-encoded string."""
        salt = secrets.token_bytes(16)
        argon2 = Argon2id(
            salt=salt,
            length=self.hash_len,
            iterations=self.iterations,
            lanes=self.lanes,
            memory_cost=self.memory_cost,
        )
        # Use derive_phc_encoded to get PHC format automatically (returns string)
        return argon2.derive_phc_encoded(password.encode("utf-8"))

    def verify(self, password: str, encoded_hash: str) -> bool:
        """Verify a password against a PHC-encoded hash."""
        try:
            Argon2id.verify_phc_encoded(password.encode("utf-8"), encoded_hash)
            return True
        except Exception:
            return False


class FieldEncryption:
    """
    Field-level encryption descriptor for SQLAlchemy models.

    Usage:
        class User(Base):
            api_key_encrypted = FieldEncryption.column("api_key")
    """

    def __init__(self, field_name: str, encryption_manager: Optional[EncryptionManager] = None):
        self.field_name = field_name
        self.encryption_manager = encryption_manager or EncryptionManager()

    def encrypt(self, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        return self.encryption_manager.encrypt(value)

    def decrypt(self, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        return self.encryption_manager.decrypt(value)

    @classmethod
    def column(cls, field_name: str, encryption_manager: Optional[EncryptionManager] = None):
        """Create an encrypted column property."""
        enc = cls(field_name, encryption_manager)

        def getter(self):
            encrypted_value = getattr(self, f"_{field_name}_encrypted", None)
            return enc.decrypt(encrypted_value)

        def setter(self, value):
            setattr(self, f"_{field_name}_encrypted", enc.encrypt(value))

        return property(getter, setter)


# Singleton instances
_encryption_manager: Optional[EncryptionManager] = None
_password_hasher: Optional[PasswordHasher] = None


def get_encryption_manager(key_path: Optional[Path] = None) -> EncryptionManager:
    """Get singleton encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager(key_path)
    return _encryption_manager


def get_password_hasher() -> PasswordHasher:
    """Get singleton password hasher."""
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = PasswordHasher()
    return _password_hasher


# Convenience functions
def encrypt_field(value: str) -> str:
    """Encrypt a single field value."""
    return get_encryption_manager().encrypt(value)


def decrypt_field(value: str) -> str:
    """Decrypt a single field value."""
    return get_encryption_manager().decrypt(value)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return get_password_hasher().hash(password)


def verify_password(password: str, hash_str: str) -> bool:
    """Verify a password against its hash."""
    return get_password_hasher().verify(password, hash_str)


# Audit logging for encryption operations
def log_encryption_operation(operation: str, field: str, success: bool, details: str = "") -> None:
    """Log encryption/decryption operations for audit trail."""
    import json
    from datetime import datetime, timezone

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "field": field,
        "success": success,
        "details": details[:200] if details else "",
    }

    log_path = Path.home() / ".jebat" / "logs" / "encryption_audit.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


__all__ = [
    "EncryptionManager",
    "PasswordHasher",
    "FieldEncryption",
    "get_encryption_manager",
    "get_password_hasher",
    "encrypt_field",
    "decrypt_field",
    "hash_password",
    "verify_password",
    "log_encryption_operation",
]