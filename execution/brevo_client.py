"""Brevo (formerly Sendinblue) transactional email client."""

import httpx

from execution.config import (
    BREVO_API_KEY,
    BREVO_SENDER_EMAIL,
    BREVO_SENDER_NAME,
)

_BREVO_URL = "https://api.brevo.com/v3/smtp/email"
_HEADERS = {
    "api-key": BREVO_API_KEY,
    "Content-Type": "application/json",
}


async def send_nurture_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
) -> str:
    """
    Send a transactional nurture email via Brevo.

    Returns the message ID on success.
    """
    payload = {
        "sender": {
            "name": BREVO_SENDER_NAME,
            "email": BREVO_SENDER_EMAIL,
        },
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_BREVO_URL, headers=_HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("messageId", "")
