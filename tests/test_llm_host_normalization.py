"""Host normalization — daemon bind addresses are not client targets.

/etc/environment on the prod VPS carries OLLAMA_HOST=0.0.0.0:11434 (the
daemon's bind address). Without normalization every client call builds an
unroutable URL while the daemon is healthy. Regression guard.
"""

from __future__ import annotations

from jebat.llm.config import load_llm_config, normalize_host


def test_bare_host_gets_scheme() -> None:
    assert normalize_host("127.0.0.1:11434") == "http://127.0.0.1:11434"


def test_bind_address_maps_to_loopback() -> None:
    assert normalize_host("0.0.0.0:11434") == "http://127.0.0.1:11434"
    assert normalize_host("http://0.0.0.0:8081") == "http://127.0.0.1:8081"


def test_ipv6_wildcard_maps_to_loopback() -> None:
    assert normalize_host("http://[::]:11434") == "http://127.0.0.1:11434"


def test_trailing_slash_removed_and_https_kept() -> None:
    assert normalize_host("https://example.com/") == "https://example.com"


def test_empty_falls_back_to_default() -> None:
    assert normalize_host("", "http://127.0.0.1:9999") == "http://127.0.0.1:9999"


def test_loader_normalizes_polluted_env(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "0.0.0.0:11434")
    monkeypatch.setenv("LLAMA_CPP_HOST", "0.0.0.0:8081")
    config = load_llm_config()
    assert config.ollama_host == "http://127.0.0.1:11434"
    assert config.llamacpp_host == "http://127.0.0.1:8081"
