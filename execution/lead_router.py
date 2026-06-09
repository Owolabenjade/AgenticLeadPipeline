"""Lead Router — routes leads based on score to Closing or Nurture agents."""

import logging

from execution import hubspot_client
from execution.monitor_agent import monitor
from execution.config import NURTURE_48H_TTL, NURTURE_7D_TTL

logger = logging.getLogger("lead_router")


@monitor("LeadRouter")
async def route_lead(
    lead_data: dict,
    score_obj: dict,
    *,
    session_key: str = "",
    lead_name: str = "",
    lead_phone: str = "",
) -> None:
    """
    Route a scored lead to the appropriate downstream agent.

    Score ranges:
        65-100 → Closing Agent (Sales Qualified)
        40-64  → Nurture Agent, 48-hour re-queue (Nurturing)
        0-39   → Nurture Agent, 7-day re-queue (Long-term Nurture)
    """
    score = score_obj.get("score", 0)
    if not isinstance(score, (int, float)):
        score = 0
    score = int(score)

    lead_name = lead_data.get("name", "Unknown")
    lead_phone = lead_data.get("e164_phone", "")
    deal_id = lead_data.get("hubspot_deal_id")

    if score >= 65:
        # Hot lead → Closing Agent
        logger.info(
            "Routing %s (score %d) to Closing Agent", lead_name, score
        )
        if deal_id:
            await hubspot_client.update_deal_stage(deal_id, "Sales Qualified")

        # Import here to avoid circular imports
        from execution.closing_agent import dispatch_closing_agent
        await dispatch_closing_agent(
            lead_data, score_obj,
            session_key=session_key,
            lead_name=lead_name,
            lead_phone=lead_phone,
        )

    elif score >= 40:
        # Warm lead → Nurture (48h)
        logger.info(
            "Routing %s (score %d) to Nurture Agent (48h)",
            lead_name, score,
        )
        if deal_id:
            await hubspot_client.update_deal_stage(deal_id, "Nurturing")

        from execution.nurture_agent import dispatch_nurture_agent
        await dispatch_nurture_agent(
            lead_data, score_obj,
            requeue_ttl=NURTURE_48H_TTL,
            session_key=session_key,
            lead_name=lead_name,
            lead_phone=lead_phone,
        )

    else:
        # Cold lead → Nurture (7d)
        logger.info(
            "Routing %s (score %d) to Nurture Agent (7d)",
            lead_name, score,
        )
        if deal_id:
            await hubspot_client.update_deal_stage(deal_id, "Long-term Nurture")

        from execution.nurture_agent import dispatch_nurture_agent
        await dispatch_nurture_agent(
            lead_data, score_obj,
            requeue_ttl=NURTURE_7D_TTL,
            session_key=session_key,
            lead_name=lead_name,
            lead_phone=lead_phone,
        )
