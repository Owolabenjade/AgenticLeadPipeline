"""Centralised configuration — loads all environment variables once."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def _require(var: str) -> str:
    """Return env var or raise with a helpful message."""
    val = os.getenv(var)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {var}")
    return val


# ── Server ──────────────────────────────────────────────────────────────
WEBHOOK_BASE_URL: str = _require("WEBHOOK_BASE_URL")

# ── Market settings ─────────────────────────────────────────────────────
PHONE_DEFAULT_COUNTRY: str = _require("PHONE_DEFAULT_COUNTRY")
LOCALE: str = os.getenv("LOCALE", "en-US")
CURRENCY_SYMBOL: str = os.getenv("CURRENCY_SYMBOL", "USD")

# ── HubSpot CRM ────────────────────────────────────────────────────────
HUBSPOT_ACCESS_TOKEN: str = _require("HUBSPOT_ACCESS_TOKEN")
HUBSPOT_PORTAL_ID: str = _require("HUBSPOT_PORTAL_ID")
HUBSPOT_SALES_OWNER_ID: str = _require("HUBSPOT_SALES_OWNER_ID")
MANUAL_REVIEW_OWNER_EMAIL: str = os.getenv("MANUAL_REVIEW_OWNER_EMAIL", "")

# ── Groq ───────────────────────────────────────────────────────────────
GROQ_API_KEY: str = _require("GROQ_API_KEY")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── VAPI ───────────────────────────────────────────────────────────────
VAPI_API_KEY: str = _require("VAPI_API_KEY")
VAPI_PHONE_NUMBER_ID: str = _require("VAPI_PHONE_NUMBER_ID")

# ── Upstash Redis ──────────────────────────────────────────────────────
UPSTASH_REDIS_URL: str = _require("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN: str = _require("UPSTASH_REDIS_TOKEN")

# ── Brevo ──────────────────────────────────────────────────────────────
BREVO_API_KEY: str = _require("BREVO_API_KEY")
BREVO_SENDER_EMAIL: str = _require("BREVO_SENDER_EMAIL")
BREVO_SENDER_NAME: str = os.getenv("BREVO_SENDER_NAME", "Lead Pipeline")

# ── Slack ──────────────────────────────────────────────────────────────
SLACK_WEBHOOK_HOT_LEADS: str = _require("SLACK_WEBHOOK_HOT_LEADS")
SLACK_WEBHOOK_SYSTEM_ALERTS: str = _require("SLACK_WEBHOOK_SYSTEM_ALERTS")
SLACK_SALES_HEAD_ID: str = _require("SLACK_SALES_HEAD_ID")

# ── Dashboard auth ──────────────────────────────────────────────────────
DASHBOARD_USERNAME: str = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD: str = _require("DASHBOARD_PASSWORD")

# ── Company / branding ──────────────────────────────────────────────────
COMPANY_NAME: str    = os.getenv("COMPANY_NAME", "Lead Pipeline")
CONTACT_EMAIL: str   = os.getenv("CONTACT_EMAIL", "")

# ── Derived constants ──────────────────────────────────────────────────
HUBSPOT_API_BASE: str = "https://api.hubapi.com"
LEAD_SESSION_TTL: int = 86_400        # 24 hours
CALL_PENDING_TTL: int = 7_200          # 2 hours
NURTURE_48H_TTL: int = 172_800         # 48 hours
NURTURE_7D_TTL: int = 604_800          # 7 days
HUBSPOT_RATE_LIMIT: int = 9            # requests per second
