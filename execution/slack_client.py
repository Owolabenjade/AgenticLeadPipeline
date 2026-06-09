"""Slack webhook client — hot lead alerts and system error notifications."""

import httpx

from execution.config import (
    SLACK_WEBHOOK_HOT_LEADS,
    SLACK_WEBHOOK_SYSTEM_ALERTS,
    SLACK_SALES_HEAD_ID,
)


async def _post_webhook(webhook_url: str, payload: dict) -> None:
    """Post a message payload to a Slack webhook."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()


async def post_hot_lead(
    brief_text: str,
    sales_head_id: str | None = None,
) -> None:
    """
    Post a hot-lead brief to the #hot-leads Slack channel.
    Tags the sales head directly in the message body.
    """
    tag = f"<@{sales_head_id or SLACK_SALES_HEAD_ID}>"
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "\U0001f525 Hot Lead Alert",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": brief_text,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"\n{tag} — please follow up within 2 hours.",
                },
            },
        ],
    }
    await _post_webhook(SLACK_WEBHOOK_HOT_LEADS, payload)


async def post_system_alert(alert_text: str) -> None:
    """
    Post a system alert to the #system-alerts Slack channel.
    """
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "\u26a0\ufe0f Pipeline Alert",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert_text,
                },
            },
        ],
    }
    await _post_webhook(SLACK_WEBHOOK_SYSTEM_ALERTS, payload)
