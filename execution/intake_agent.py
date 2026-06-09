"""Intake Agent — validates, normalises, and ingests incoming leads."""

import logging

from execution.config import PHONE_DEFAULT_COUNTRY
from execution.phone_normalizer import normalise_phone
from execution.qa_checks import validate_lead_payload, validate_email, normalise_budget, deduplicate_contact
from execution import redis_client, hubspot_client
from execution.monitor_agent import monitor
from execution.call_agent import dispatch_call_agent

logger = logging.getLogger("intake_agent")


@monitor("IntakeAgent")
async def process_lead(
    payload: dict,
    *,
    session_key: str = "",
    lead_name: str = "",
    lead_phone: str = "",
) -> dict | None:
    """
    Full intake pipeline for a single lead submission.

    Returns the enriched lead data dict on success, None on failure.
    """
    # 1. Validate required fields
    is_valid, error_msg = validate_lead_payload(payload)
    if not is_valid:
        logger.warning("Rejected lead: %s", error_msg)
        raise ValueError(error_msg)

    raw_name = payload["name"].strip()
    raw_phone = payload["phone"].strip()
    raw_email = (payload.get("email") or "").strip()
    interest = (payload.get("interest") or "").strip()
    raw_budget = (payload.get("budget") or "").strip()
    location = (payload.get("location") or "").strip()
    source = (payload.get("source") or "website").strip()

    # 2. Normalise phone number
    e164_phone = normalise_phone(raw_phone, PHONE_DEFAULT_COUNTRY)

    # 3. Validate email
    email_valid = validate_email(raw_email) if raw_email else False

    # 4. Normalise budget
    budget_normalised = normalise_budget(raw_budget)

    # 5. Build enriched lead record
    lead_data = {
        "name": raw_name,
        "phone_raw": raw_phone,
        "e164_phone": e164_phone,
        "email": raw_email if email_valid else "",
        "email_valid": email_valid,
        "interest": interest,
        "budget_raw": raw_budget,
        "budget_normalised": budget_normalised,
        "location": location,
        "source": source,
    }

    # 6. Deduplicate & create/update in HubSpot
    existing_contact_id = await deduplicate_contact(
        e164_phone, raw_email, hubspot_client
    )

    if existing_contact_id:
        # Update existing contact
        update_props = {
            "phone": e164_phone,
            "lead_property_interest": interest,
            "lead_budget": str(budget_normalised or ""),
            "lead_preferred_location": location,
            "lead_source_channel": source,
        }
        if email_valid:
            update_props["email"] = raw_email
        await hubspot_client.update_contact(existing_contact_id, update_props)
        contact_id = existing_contact_id
        logger.info("Updated existing contact %s", contact_id)
    else:
        # Create new contact
        contact_id = await hubspot_client.create_contact(lead_data)
        logger.info("Created new contact %s", contact_id)

    lead_data["hubspot_contact_id"] = contact_id

    # 7. Create deal with initial stage
    deal_id = await hubspot_client.create_deal_for_contact(
        contact_id, raw_name, "Contacted - Pending Call"
    )
    lead_data["hubspot_deal_id"] = deal_id

    # 8. Store session in Redis
    session_key = await redis_client.set_lead_session(e164_phone, lead_data)
    lead_data["session_key"] = session_key

    # 9. Dispatch Call Agent
    await dispatch_call_agent(lead_data, session_key=session_key)

    return lead_data
