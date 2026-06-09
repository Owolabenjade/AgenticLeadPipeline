"""Monitor Agent — pipeline error handling, logging, and Slack alerts."""

import functools
import json
import logging
import traceback
import time
from pathlib import Path
from typing import Any, Callable

from execution import redis_client, slack_client

# Ensure logs directory exists
_LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOGS_DIR.mkdir(exist_ok=True)
_FAILED_LEADS_LOG = _LOGS_DIR / "failed_leads.jsonl"

logger = logging.getLogger("monitor_agent")


def _mask_phone(phone: str) -> str:
    """Mask phone to show only last 4 digits."""
    if len(phone) > 4:
        return "*" * (len(phone) - 4) + phone[-4:]
    return phone


def _log_failed_lead(error_record: dict) -> None:
    """Append an error record to the failed_leads JSONL log."""
    with open(_FAILED_LEADS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_record) + "\n")


def monitor(agent_name: str) -> Callable:
    """
    Decorator that wraps agent functions with error handling.

    On any unhandled exception:
    1. Extracts error details
    2. Writes error to Redis
    3. Posts alert to Slack #system-alerts
    4. Logs to failed_leads.jsonl
    5. Does NOT re-raise — exits gracefully
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                # Extract context from kwargs or args
                session_key = kwargs.get("session_key", "unknown")
                lead_name = kwargs.get("lead_name", "Unknown")
                lead_phone = kwargs.get("lead_phone", "")

                error_type = type(exc).__name__
                stack_summary = traceback.format_exc()[-500:]  # last 500 chars
                timestamp = int(time.time())

                error_record = {
                    "agent": agent_name,
                    "session_key": session_key,
                    "lead_name": lead_name,
                    "phone_masked": _mask_phone(lead_phone),
                    "error_type": error_type,
                    "error_message": str(exc)[:300],
                    "stack_trace": stack_summary,
                    "timestamp": timestamp,
                }

                # 1. Log locally
                logger.error(
                    "Agent %s failed for session %s: %s",
                    agent_name, session_key, exc,
                )
                _log_failed_lead(error_record)

                # 2. Write to Redis (best-effort)
                try:
                    await redis_client.write_error(session_key, error_record)
                except Exception as redis_err:
                    logger.error("Failed to write error to Redis: %s", redis_err)

                # 3. Post Slack alert (best-effort, within 30 seconds)
                try:
                    masked = _mask_phone(lead_phone)
                    alert_text = (
                        f"*Agent:* `{agent_name}`\n"
                        f"*Lead:* {lead_name} ({masked})\n"
                        f"*Error:* `{error_type}` — {str(exc)[:200]}\n"
                        f"*Suggested fix:* Check `logs/failed_leads.jsonl` "
                        f"and re-run the `{agent_name}` stage manually."
                    )
                    await slack_client.post_system_alert(alert_text)
                except Exception as slack_err:
                    logger.error("Failed to post Slack alert: %s", slack_err)

                # Gracefully return None — never re-raise
                return None

        return wrapper

    return decorator
