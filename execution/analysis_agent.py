"""Analysis Agent — scores call transcripts and updates CRM."""

import logging

from execution import redis_client, hubspot_client
from execution.groq_client import analyse_transcript
from execution.lead_router import route_lead
from execution.monitor_agent import monitor
from execution.config import MANUAL_REVIEW_OWNER_EMAIL, HUBSPOT_SALES_OWNER_ID

logger = logging.getLogger("analysis_agent")


@monitor("AnalysisAgent")
async def process_transcript(
    transcript_text: str,
    session_key: str,
    *,
    lead_name: str = "",
    lead_phone: str = "",
) -> dict | None:
    """
    Analyse a VAPI call transcript, score the lead, and dispatch routing.

    Returns the score object on success, None on failure.
    """
    # 1. Retrieve lead data from Redis
    lead_data = await redis_client.get_lead_session(session_key)
    if not lead_data:
        logger.error("No lead session found for key: %s", session_key)
        raise ValueError(f"Lead session not found: {session_key}")

    lead_name = lead_data.get("name", "Unknown")
    lead_phone = lead_data.get("e164_phone", "")
    contact_id = lead_data.get("hubspot_contact_id")
    deal_id = lead_data.get("hubspot_deal_id")

    # 2. Analyse transcript via Groq (JSON mode)
    logger.info("Analysing transcript for %s", lead_name)
    score_obj = await analyse_transcript(transcript_text)

    # 3. Validate score object has required fields
    required_fields = [
        "score", "intent_strength", "budget_confirmed",
        "timeline", "objections", "summary_notes", "confidence",
    ]
    for field in required_fields:
        if field not in score_obj:
            logger.warning("Missing field in score object: %s", field)
            score_obj.setdefault(field, None)

    # 4. Handle low-confidence scores
    confidence = score_obj.get("confidence", 0)
    if isinstance(confidence, (int, float)) and confidence < 0.6:
        logger.info(
            "Low confidence (%.2f) for %s — flagging for manual review",
            confidence, lead_name,
        )
        if contact_id:
            # Create a manual review task in HubSpot
            await hubspot_client.create_task(
                contact_id,
                f"Manual review required — AI confidence {confidence:.0%}",
                HUBSPOT_SALES_OWNER_ID,
            )

    # 5. Write score to Redis
    await redis_client.write_score(session_key, score_obj)

    # 6. Update HubSpot contact with scored fields
    if contact_id:
        score_props = {
            "lead_score": str(score_obj.get("score", 0)),
            "lead_intent_strength": str(score_obj.get("intent_strength", "")),
            "lead_budget_confirmed": str(score_obj.get("budget_confirmed", False)).lower(),
            "lead_timeline": str(score_obj.get("timeline", "")),
            "lead_confidence": str(score_obj.get("confidence", 0)),
            "lead_call_summary": str(score_obj.get("summary_notes", "")),
        }
        await hubspot_client.update_contact(contact_id, score_props)

    # 7. Dispatch routing
    lead_data["score"] = score_obj
    lead_data["transcript"] = transcript_text
    await route_lead(lead_data, score_obj, session_key=session_key)

    return score_obj
