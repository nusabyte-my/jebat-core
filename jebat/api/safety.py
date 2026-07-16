"""Guards for externally impactful API actions."""

from __future__ import annotations

import os

from fastapi import HTTPException


def require_action_confirmation(value: str | None, action: str) -> None:
    """Require an explicit confirmation header for production actions."""
    if os.getenv("JEBAT_ENV", "development").lower() != "production":
        return
    if value != action:
        raise HTTPException(
            status_code=428,
            detail=f"Set X-JEBAT-Action-Confirm: {action} to confirm this action.",
        )
