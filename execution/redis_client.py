"""Upstash Redis client via REST API — no TCP connections needed."""

import json
import time
from typing import Any, Optional

import httpx

from execution.config import (
    UPSTASH_REDIS_URL,
    UPSTASH_REDIS_TOKEN,
    LEAD_SESSION_TTL,
    CALL_PENDING_TTL,
)

_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}",
    "Content-Type": "application/json",
}


async def _execute(command: list) -> Any:
    """Execute a single Redis command via Upstash REST API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            UPSTASH_REDIS_URL,
            headers=_HEADERS,
            json=command,
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("result")


async def set_lead_session(
    e164_phone: str, data: dict, ttl: int = LEAD_SESSION_TTL
) -> str:
    """Store a lead session. Returns the session key."""
    ts = int(time.time())
    key = f"lead:{e164_phone}:{ts}"
    await _execute(["SET", key, json.dumps(data), "EX", str(ttl)])
    return key


async def get_lead_session(session_key: str) -> Optional[dict]:
    """Retrieve a lead session by key."""
    result = await _execute(["GET", session_key])
    if result is None:
        return None
    return json.loads(result)


async def set_call_pending(
    session_key: str, ttl: int = CALL_PENDING_TTL
) -> None:
    """Set the call_pending flag with a 2-hour TTL."""
    flag_key = f"call_pending:{session_key}"
    await _execute(["SET", flag_key, "1", "EX", str(ttl)])


async def write_score(session_key: str, score_data: dict) -> None:
    """Write the full score object to Redis."""
    score_key = f"score:{session_key}"
    await _execute(
        ["SET", score_key, json.dumps(score_data), "EX", str(LEAD_SESSION_TTL)]
    )


async def enqueue_nurture(session_key: str, ttl: int) -> None:
    """Add a lead to the nurture re-queue with the specified TTL."""
    nurture_key = f"nurture:{session_key}"
    await _execute(["SET", nurture_key, "1", "EX", str(ttl)])


async def write_error(
    session_id: str, error_data: dict
) -> str:
    """Write an error record. Returns the error key."""
    ts = int(time.time())
    key = f"error:{session_id}:{ts}"
    await _execute(
        ["SET", key, json.dumps(error_data), "EX", str(LEAD_SESSION_TTL)]
    )
    return key
