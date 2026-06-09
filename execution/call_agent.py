"""Call Agent — generates call script and triggers outbound VAPI call."""

import logging

from execution import redis_client
from execution.groq_client import generate_call_script
from execution.vapi_client import trigger_outbound_call, VAPICallError
from execution.monitor_agent import monitor

logger = logging.getLogger("call_agent")


@monitor("CallAgent")
async def dispatch_call_agent(
    lead_data: dict,
    *,
    session_key: str = "",
    lead_name: str = "",
    lead_phone: str = "",
) -> dict | None:
    """
    Generate a call script via Groq and trigger an outbound call via VAPI.

    Returns updated lead_data with call info, or None if VAPI fails.
    """
    lead_name = lead_data.get("name", "Unknown")
    lead_phone = lead_data.get("e164_phone", "")

    # 1. Generate personalised call script
    logger.info("Generating call script for %s", lead_name)
    script = await generate_call_script(lead_data)
    lead_data["call_script"] = script

    # 2. Trigger outbound call via VAPI
    try:
        call_id = await trigger_outbound_call(
            e164_phone=lead_phone,
            script=script,
            session_key=session_key,
        )
        lead_data["vapi_call_id"] = call_id
        logger.info("VAPI call initiated: %s", call_id)

        # 3. Set call_pending flag in Redis (2-hour TTL)
        await redis_client.set_call_pending(session_key)

    except VAPICallError as exc:
        # Log to Monitor Agent and skip call stage — don't block the pipeline
        logger.error("VAPI call failed for %s: %s", lead_name, exc)
        lead_data["call_status"] = "failed"
        lead_data["call_error"] = str(exc)
        return lead_data

    lead_data["call_status"] = "initiated"
    return lead_data
