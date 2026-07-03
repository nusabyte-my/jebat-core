# Q3 2026 Sprint 7-8: Python SDK

## Objective
Create a production-ready Python SDK for the JEBAT REST API that can be installed via `pip install jebat-sdk`.

## Requirements
- Async/await support with httpx
- Full type hints with Pydantic models
- Sync and async clients
- Retry logic with exponential backoff
- WebSocket support for streaming
- Comprehensive test coverage
- Published to PyPI

## Package Structure
```
jebat_sdk/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── src/
│   └── jebat_sdk/
│       ├── __init__.py
│       ├── client.py
│       ├── async_client.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── chat.py
│       │   ├── memories.py
│       │   ├── agents.py
│       │   ├── channels.py
│       │   ├── monitoring.py
│       │   └── common.py
│       ├── exceptions.py
│       ├── retry.py
│       └── websocket.py
└── tests/
    ├── __init__.py
    ├── test_client.py
    ├── test_async_client.py
    ├── test_models.py
    └── test_retry.py
```

## Sprint 7: Core Client & Models (Week 1)
- [ ] Project setup with pyproject.toml
- [ ] Pydantic models for all API endpoints
- [ ] Base sync client with httpx
- [ ] Auth helpers (login, refresh, API keys)
- [ ] Retry logic with tenacity

## Sprint 8: Async Client & Streaming (Week 2)
- [ ] Async client with httpx.AsyncClient
- [ ] WebSocket support for streaming chat
- [ ] Context manager support
- [ ] Comprehensive tests
- [ ] PyPI publishing workflow