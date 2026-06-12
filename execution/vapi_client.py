"""VAPI.ai client — outbound call triggering with international fallback handling."""

import asyncio
import logging
from typing import Optional

import httpx

from execution.config import (
    VAPI_API_KEY,
    VAPI_PHONE_NUMBER_ID,
    WEBHOOK_BASE_URL,
)

logger = logging.getLogger(__name__)

_VAPI_BASE = "https://api.vapi.ai"
_HEADERS = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json",
}

# Error messages VAPI returns for international restriction
_INTL_ERROR_PHRASES = [
    "international calls",
    "free vapi numbers do not support",
    "subscriptionlimits",
    "country not supported",
]


class VAPICallError(Exception):
    """Raised when VAPI fails to initiate a call after retries."""
    pass


class VAPIInternationalError(VAPICallError):
    """Raised when the phone number requires international calling (not on free plan)."""
    pass


def _is_international_error(response_text: str) -> bool:
    text_lower = response_text.lower()
    return any(phrase in text_lower for phrase in _INTL_ERROR_PHRASES)


async def trigger_outbound_call(
    e164_phone: str,
    script: str,
    session_key: str,
) -> Optional[str]:
    """
    Trigger an outbound call via VAPI.

    Returns the call ID on success (HTTP 201).
    Raises VAPIInternationalError if the number requires international calling
    (free VAPI plan restriction — needs Twilio number imported into VAPI).
    Raises VAPICallError for all other failures after one retry.
    """
    callback_url = f"{WEBHOOK_BASE_URL}/vapi/transcript"

    payload = {
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {"number": e164_phone},
        "assistant": {
            "firstMessage": script[:500],
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
            resp = await client.post(
                f"{_VAPI_BASE}/call/phone",
                headers=_HEADERS,
                json=payload,
            )

            if resp.status_code == 201:
                data = resp.json()
                call_id = data.get("id")
                logger.info("VAPI call dispatched: call_id=%s to=%s", call_id, e164_phone)
                return call_id

            # Detect international restriction immediately — no retry needed
            if resp.status_code == 400 and _is_international_error(resp.text):
                raise VAPIInternationalError(
                    f"VAPI free number cannot call international numbers ({e164_phone}). "
                    "To fix: import a Twilio number into VAPI dashboard → "
                    "vapi.ai/phone-numbers → Import → Twilio. "
                    "Then update VAPI_PHONE_NUMBER_ID in your .env."
                )

            if attempt == 0:
                logger.warning(
                    "VAPI attempt 1 failed (HTTP %s) — retrying in 5s: %s",
                    resp.status_code, resp.text[:200],
                )
                await asyncio.sleep(5)
                continue

            raise VAPICallError(
                f"VAPI call failed after retry: HTTP {resp.status_code} — {resp.text[:300]}"
            )

    return None
