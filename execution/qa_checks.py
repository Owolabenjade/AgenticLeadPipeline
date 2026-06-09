"""Quality assurance checks — validation, deduplication, normalisation."""

import re
from typing import Optional


# RFC 5322 simplified email regex
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def validate_email(email: str) -> bool:
    """Validate email against RFC 5322 format."""
    if not email or not isinstance(email, str):
        return False
    return bool(_EMAIL_RE.match(email.strip()))


def validate_lead_payload(payload: dict) -> tuple[bool, Optional[str]]:
    """
    Validate a lead payload has required fields.

    Returns:
        (is_valid, error_message)
    """
    name = payload.get("name", "").strip()
    phone = payload.get("phone", "").strip()

    if not name:
        return False, "Missing required field: name"
    if not phone:
        return False, "Missing required field: phone"

    return True, None


def normalise_budget(raw_budget: str) -> Optional[int]:
    """
    Strip symbols, commas, shorthand and return a plain integer.

    Handles: '1.5m', '500k', 'NGN 50,000,000', '$1,200,000', '2.5M', etc.
    Returns None if unparseable.
    """
    if not raw_budget:
        return None

    text = str(raw_budget).strip().lower()

    # Remove common currency symbols and letters (keep digits, dots, commas, k/m/b)
    text = re.sub(r"[^\d.,kmb]", "", text)

    if not text:
        return None

    multiplier = 1
    if text.endswith("b"):
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]

    # Remove commas
    text = text.replace(",", "")

    try:
        return int(float(text) * multiplier)
    except (ValueError, OverflowError):
        return None


async def deduplicate_contact(
    e164_phone: str, email: str, hubspot_client
) -> Optional[str]:
    """
    Check if a contact already exists by phone or email.

    Returns the existing HubSpot contact ID if found, None otherwise.
    """
    # Search by phone first
    contact_id = await hubspot_client.search_contact_by_phone(e164_phone)
    if contact_id:
        return contact_id

    # Fallback: search by email
    if email and validate_email(email):
        contact_id = await hubspot_client.search_contact_by_email(email)
        if contact_id:
            return contact_id

    return None
