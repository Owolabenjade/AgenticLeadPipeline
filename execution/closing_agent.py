"""Closing Agent — handles qualified (hot) leads."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from execution import hubspot_client, slack_client
from execution.monitor_agent import monitor
from execution.config import CURRENCY_SYMBOL, HUBSPOT_SALES_OWNER_ID

logger = logging.getLogger("closing_agent")

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
)


@monitor("ClosingAgent")
async def dispatch_closing_agent(
    lead_data: dict,
    score_obj: dict,
    *,
    session_key: str = "",
    lead_name: str = "",
    lead_phone: str = "",
) -> None:
    """
    Generate a lead brief, post to Slack, and create a HubSpot follow-up task.
    """
    lead_name = lead_data.get("name", "Unknown")
    contact_id = lead_data.get("hubspot_contact_id")

    # 1. Render lead brief from Jinja2 template
    template = _jinja_env.get_template("lead_brief.jinja2")
    brief_text = template.render(
        name=lead_name,
        phone=lead_data.get("e164_phone", ""),
        email=lead_data.get("email", ""),
        interest=lead_data.get("interest", ""),
        location=lead_data.get("location", ""),
        budget=lead_data.get("budget_normalised", ""),
        currency=CURRENCY_SYMBOL,
        score=score_obj.get("score", 0),
        intent=score_obj.get("intent_strength", ""),
        timeline=score_obj.get("timeline", ""),
        summary=score_obj.get("summary_notes", ""),
        objections=score_obj.get("objections", []),
        confidence=score_obj.get("confidence", 0),
    )

    # 2. Post to Slack #hot-leads
    logger.info("Posting hot-lead brief for %s to Slack", lead_name)
    await slack_client.post_hot_lead(brief_text)

    # 3. Create HubSpot task: "Call within 2 hours"
    if contact_id:
        await hubspot_client.create_task(
            contact_id,
            f"Call within 2 hours — {lead_name}",
            HUBSPOT_SALES_OWNER_ID,
        )
        logger.info("Created follow-up task for contact %s", contact_id)
