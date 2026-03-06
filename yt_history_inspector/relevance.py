from __future__ import annotations

from typing import Optional


def hide_reason(reason: Optional[str]) -> str:
    return (reason or "").strip() or "manual"
