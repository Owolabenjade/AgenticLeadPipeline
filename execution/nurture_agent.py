"""Nurture Agent — handles unqualified and warm leads."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from execution import redis_client, hubspot_client
from execution.brevo_client import send_nurture_email
from execution.monitor_agent import monitor
from execution.config import CURRENCY_SYMBOL

logger = logging.getLogger("nurture_agent")

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,
)


@monitor("NurtureAgent")
async def dispatch_nurture_agent(
    lead_data: dict,
    score_obj: dict,
    requeue_ttl: int,
    *,
    session_key: str = "",
    lead_name: str = "",
    lead_phone: str = "",
) -> None:
    """
    Send a nurture email and enqueue the lead for re-contact.
    """
    lead_name = lead_data.get("name", "Unknown")
    lead_email = lead_data.get("email", "")
    interest = lead_data.get("interest", "property")
    location = lead_data.get("location", "")

    if not lead_email:
        logger.warning("No email for %s — skipping nurture email", lead_name)
    else:
        # 1. Render nurture email from Jinja2 template
        template = _jinja_env.get_template("nurture_email.jinja2")
        html_content = template.render(
            name=lead_name,
            first_name=lead_name.split()[0] if lead_name else "there",
            interest=interest,
            location=location,
            budget=lead_data.get("budget_normalised", ""),
            currency=CURRENCY_SYMBOL,
            score=score_obj.get("score", 0),
            summary=score_obj.get("summary_notes", ""),
        )

        subject = f"Your {interest} enquiry in {location}" if location else f"Your {interest} enquiry"

        # 2. Send via Brevo
        logger.info("Sending nurture email to %s", lead_email)
        await send_nurture_email(
            to_email=lead_email,
            to_name=lead_name,
            subject=subject,
            html_content=html_content,
        )

    # 3. Add to Redis re-queue with TTL
    if session_key:
        await redis_client.enqueue_nurture(session_key, requeue_ttl)
        logger.info(
            "Enqueued %s for nurture re-contact (TTL=%ds)",
            lead_name, requeue_ttl,
        )
