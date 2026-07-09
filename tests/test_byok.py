"""Tests for BYOK module — key storage, encryption, provider detection."""

import json
import os
import tempfile
import pytest
from pathlib import Path

from jebat.features.byok.storage import (
    KeyStorage,
    KeyInfo,
    encrypt_key,
    decrypt_key,
    detect_provider,
)
from jebat.features.byok.adapters import (
    list_supported_providers,
)


class TestKeyEncryption:
    """Encryption roundtrip."""

    def test_encrypt_decrypt_roundtrip(self):
        key = "sk-abc123def456"
        encrypted = encrypt_key(key)
        assert encrypted != key
        decrypted = decrypt_key(encrypted)
        assert decrypted == key

    def test_differs_each_time(self):
        """Same key produces different ciphertext due to random salt."""
        key = "sk-test-key"
        e1 = encrypt_key(key)
        e2 = encrypt_key(key)
        assert e1 != e2


class TestProviderDetection:
    """Auto-detection from key prefix."""

    def test_openai(self):
        assert detect_provider("sk-abc123") == "openai"
        assert detect_provider("sk-proj-xyz") == "openai"

    def test_anthropic(self):
        assert detect_provider("sk-ant-abc123") == "anthropic"

    def test_google(self):
        assert detect_provider("AIzaSyABC123") == "google"

    def test_groq(self):
        assert detect_provider("gsk_abc123") == "groq"

    def test_openrouter(self):
        assert detect_provider("sk-or-abc123") == "openrouter"

    def test_unknown(self):
        assert detect_provider("xyz-unknown-key") == "unknown"


class TestKeyStorage:
    """KeyStorage CRUD and persistence."""

    @pytest.fixture
    def storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = KeyStorage(tmp)
            yield s

    def test_add_key(self, storage):
        info = storage.add_key("sk-test-key-12345", provider="openai", label="Test Key")
        assert info.id.startswith("key-")
        assert info.provider == "openai"
        assert info.label == "Test Key"
        assert "..." in info.key_prefix

    def test_get_key(self, storage):
        info = storage.add_key("sk-secret-abc", provider="openai")
        retrieved = storage.get_key(info.id)
        assert retrieved == "sk-secret-abc"

    def test_get_key_not_found(self, storage):
        with pytest.raises(KeyError):
            storage.get_key("nonexistent")

    def test_list_keys(self, storage):
        storage.add_key("sk-111", provider="openai")
        storage.add_key("sk-ant-222", provider="anthropic")
        keys = storage.list_keys()
        assert len(keys) == 2
        # No raw keys in output
        for k in keys:
            assert not k.id.startswith("sk-")
            assert "..." in k.key_prefix

    def test_remove_key(self, storage):
        info = storage.add_key("sk-temp", provider="openai")
        assert storage.remove_key(info.id) is True
        assert storage.count() == 0
        assert storage.remove_key("nonexistent") is False

    def test_mark_verified(self, storage):
        info = storage.add_key("sk-test", provider="openai")
        storage.mark_verified(info.id, True)
        updated = storage.get_key_info(info.id)
        assert updated is not None
        assert updated.is_valid is True
        assert updated.last_verified != ""

    def test_persistence(self, storage):
        storage.add_key("sk-persist", provider="openai")
        # Create a new storage instance pointing to same dir
        storage2 = KeyStorage(storage.storage_dir)
        assert storage2.count() == 1

    def test_auto_detect_provider_on_add(self, storage):
        info = storage.add_key("sk-ant-test123")
        assert info.provider == "anthropic"

    def test_providers_list(self, storage):
        storage.add_key("sk-openai-1", provider="openai")
        storage.add_key("sk-ant-1", provider="anthropic")
        providers = storage.providers()
        assert "openai" in providers
        assert "anthropic" in providers


class TestAdapterRegistry:
    """Provider adapter registry."""

    def test_supported_providers(self):
        providers = list_supported_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers
        assert "groq" in providers
        assert "openrouter" in providers
