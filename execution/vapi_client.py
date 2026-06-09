"""VAPI.ai client — outbound call triggering."""

import asyncio
from typing import Optional

import httpx

from execution.config import (
    VAPI_API_KEY,
    VAPI_PHONE_NUMBER_ID,
    WEBHOOK_BASE_URL,
)

_VAPI_URL = "https://api.vapi.ai/call/phone"
_HEADERS = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json",
}


class VAPICallError(Exception):
    """Raised when VAPI fails to initiate a call after retries."""
    pass


async def trigger_outbound_call(
    e164_phone: str,
    script: str,
    session_key: str,
) -> Optional[str]:
    """
    Trigger an outbound call via VAPI.

    Returns the call ID on success (HTTP 201).
    Retries once after 5 seconds on failure.
    Raises VAPICallError if both attempts fail.
    """
    callback_url = f"{WEBHOOK_BASE_URL}/vapi/transcript"

    payload = {
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {"number": e164_phone},
        "assistant": {
            "firstMessage": script[:500],  # VAPI first message limit
            "model": {
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": script,
                    }
                ],
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM",
            },
        },
        "serverUrl": callback_url,
        "metadata": {"session_key": session_key},
    }

    for attempt in range(2):
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(_VAPI_URL, headers=_HEADERS, json=payload)

            if resp.status_code == 201:
                data = resp.json()
                return data.get("id")

            if attempt == 0:
                await asyncio.sleep(5)
                continue

            raise VAPICallError(
                f"VAPI call failed after retry: HTTP {resp.status_code} — {resp.text}"
            )

    return None
