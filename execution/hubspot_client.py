"""HubSpot CRM client — contacts, deals, properties, and pipeline setup."""

import asyncio
import datetime
import time
from typing import Any, Optional

import httpx

from execution.config import (
    HUBSPOT_ACCESS_TOKEN,
    HUBSPOT_API_BASE,
    HUBSPOT_RATE_LIMIT,
    HUBSPOT_SALES_OWNER_ID,
    MANUAL_REVIEW_OWNER_EMAIL,
)

_HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

# Token-bucket rate limiter: 9 requests per second
_semaphore = asyncio.Semaphore(HUBSPOT_RATE_LIMIT)
_last_request_time = 0.0


async def _rate_limited_request(
    method: str, url: str, **kwargs
) -> httpx.Response:
    """Make a rate-limited HTTP request to HubSpot."""
    global _last_request_time
    async with _semaphore:
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < (1.0 / HUBSPOT_RATE_LIMIT):
            await asyncio.sleep((1.0 / HUBSPOT_RATE_LIMIT) - elapsed)
        _last_request_time = time.monotonic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method, url, headers=_HEADERS, **kwargs
            )
            resp.raise_for_status()
            return resp


def format_custom_props_to_desc(properties: dict) -> str:
    """Helper to format custom properties into a description block."""
    lines = ["--- AI Lead Pipeline Custom Fields ---"]
    custom_props = [
        "lead_property_interest",
        "lead_budget",
        "lead_preferred_location",
        "lead_source_channel",
        "lead_score",
        "lead_intent_strength",
        "lead_budget_confirmed",
        "lead_timeline",
        "lead_confidence",
        "lead_call_summary",
    ]
    for key in custom_props:
        if key in properties and properties[key] not in (None, ""):
            label = key.replace("lead_", "").replace("_", " ").title()
            lines.append(f"{label}: {properties[key]}")
    if len(lines) == 1:
        return ""
    return "\n".join(lines)


async def create_note_for_contact(contact_id: str, note_body: str) -> None:
    """Create a note associated with a contact."""
    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/notes"
    now_iso = datetime.datetime.now(datetime.UTC).isoformat()

    payload = {
        "properties": {
            "hs_note_body": note_body.replace("\n", "<br>"),
            "hubspot_owner_id": HUBSPOT_SALES_OWNER_ID,
            "hs_timestamp": now_iso
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 202  # Note to contact association type ID
                    }
                ]
            }
        ]
    }
    await _rate_limited_request("POST", url, json=payload)


# ── Contact Operations ──────────────────────────────────────────────────


async def search_contact_by_phone(e164_phone: str) -> Optional[str]:
    """Search for a contact by E.164 phone. Returns contact ID or None."""
    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "phone",
                        "operator": "EQ",
                        "value": e164_phone,
                    }
                ]
            }
        ],
        "properties": ["phone", "email", "firstname", "lastname"],
        "limit": 1,
    }
    resp = await _rate_limited_request("POST", url, json=payload)
    data = resp.json()
    results = data.get("results", [])
    if results:
        return results[0]["id"]
    return None


async def search_contact_by_email(email: str) -> Optional[str]:
    """Search for a contact by email. Returns contact ID or None."""
    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email,
                    }
                ]
            }
        ],
        "properties": ["phone", "email", "firstname", "lastname"],
        "limit": 1,
    }
    resp = await _rate_limited_request("POST", url, json=payload)
    data = resp.json()
    results = data.get("results", [])
    if results:
        return results[0]["id"]
    return None


async def create_contact(lead_data: dict) -> str:
    """Create a new HubSpot contact. Returns the contact ID."""
    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts"
    name_parts = lead_data.get("name", "").strip().split(" ", 1)
    firstname = name_parts[0] if name_parts else ""
    lastname = name_parts[1] if len(name_parts) > 1 else ""

    properties = {
        "firstname": firstname,
        "lastname": lastname,
        "phone": lead_data.get("e164_phone", ""),
        "email": lead_data.get("email", ""),
        "hs_lead_status": "NEW",
        "lead_property_interest": lead_data.get("interest", ""),
        "lead_budget": str(lead_data.get("budget_normalised", "")),
        "lead_preferred_location": lead_data.get("location", ""),
        "lead_source_channel": lead_data.get("source", ""),
    }
    
    try:
        resp = await _rate_limited_request(
            "POST", url, json={"properties": properties}
        )
        return resp.json()["id"]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400 and "PROPERTY_DOESNT_EXIST" in exc.response.text:
            # Fallback: remove custom properties, put them in a Note instead
            fallback_properties = {
                "firstname": firstname,
                "lastname": lastname,
                "phone": lead_data.get("e164_phone", ""),
                "email": lead_data.get("email", ""),
                "hs_lead_status": "NEW",
            }
            resp = await _rate_limited_request(
                "POST", url, json={"properties": fallback_properties}
            )
            contact_id = resp.json()["id"]
            
            desc_text = format_custom_props_to_desc(properties)
            if desc_text:
                try:
                    await create_note_for_contact(contact_id, desc_text)
                except Exception as e:
                    print(f"Failed to create fallback note: {e}")
            
            return contact_id
        raise


async def update_contact(contact_id: str, properties: dict) -> None:
    """Update an existing HubSpot contact."""
    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
    try:
        await _rate_limited_request(
            "PATCH", url, json={"properties": properties}
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400 and "PROPERTY_DOESNT_EXIST" in exc.response.text:
            # Fallback: remove custom properties, format to note instead
            standard_keys = {"firstname", "lastname", "phone", "email", "hs_lead_status"}
            fallback_properties = {k: v for k, v in properties.items() if k in standard_keys}
            if fallback_properties:
                await _rate_limited_request(
                    "PATCH", url, json={"properties": fallback_properties}
                )
            
            desc_text = format_custom_props_to_desc(properties)
            if desc_text:
                try:
                    await create_note_for_contact(contact_id, desc_text)
                except Exception as e:
                    print(f"Failed to create fallback note on update: {e}")
        else:
            raise


# ── Deal Operations ─────────────────────────────────────────────────────

_PIPELINE_NAME = "Lead Conversion Pipeline"
_DEAL_STAGES = {
    "Contacted - Pending Call": {"label": "Contacted - Pending Call", "displayOrder": 0},
    "Sales Qualified": {"label": "Sales Qualified", "displayOrder": 1},
    "Nurturing": {"label": "Nurturing", "displayOrder": 2},
    "Long-term Nurture": {"label": "Long-term Nurture", "displayOrder": 3},
    "Closed Won": {"label": "Closed Won", "displayOrder": 4},
    "Closed Lost": {"label": "Closed Lost", "displayOrder": 5},
}

# Cache pipeline/stage IDs after first lookup
_pipeline_id: Optional[str] = None
_stage_ids: dict[str, str] = {}


async def ensure_pipeline_exists() -> str:
    """
    Resolve the deal pipeline to use. Strategy:
    1. Return cached value if already resolved.
    2. Fetch all pipelines from HubSpot and use the first one found
       (avoids trying to CREATE a pipeline, which requires a paid plan).
    3. Map our logical stage names to the real stage IDs from that pipeline.
    4. Fall back to hard-coded IDs from the portal if fetch fails.
    """
    global _pipeline_id, _stage_ids

    if _pipeline_id:
        return _pipeline_id

    # Hard-coded fallback using the real stage IDs from Benjamin's portal
    # (from debug_hubspot.py output — "Buyers pipeline", id=default)
    _FALLBACK_STAGE_MAP = {
        "Contacted - Pending Call": "5506141375",  # Buyer qualification
        "Sales Qualified":          "5506141376",  # Property selection
        "Nurturing":                "5506141377",  # Property viewing
        "Long-term Nurture":        "5506141378",  # Offer draft
        "Closed Won":               "5506141381",  # Property sold/closed won
        "Closed Lost":              "5506141382",  # Closed lost
    }

    try:
        url = f"{HUBSPOT_API_BASE}/crm/v3/pipelines/deals"
        resp = await _rate_limited_request("GET", url)
        pipelines = resp.json().get("results", [])

        if not pipelines:
            _pipeline_id = "default"
            _stage_ids = _FALLBACK_STAGE_MAP
            return _pipeline_id

        # Use the first pipeline — no creation attempt
        chosen = pipelines[0]
        _pipeline_id = chosen["id"]

        # Build a map from our logical names to real stage IDs
        # by matching on label keywords
        real_stages = {s["label"]: s["id"] for s in chosen.get("stages", [])}

        keyword_map = {
            "Contacted - Pending Call": ["qualification", "new", "contact", "pending"],
            "Sales Qualified":          ["selection", "qualified", "hot"],
            "Nurturing":                ["viewing", "nurtur", "warm"],
            "Long-term Nurture":        ["offer", "long", "cold"],
            "Closed Won":               ["won", "sold", "closed won"],
            "Closed Lost":              ["lost", "closed lost"],
        }

        for logical_name, keywords in keyword_map.items():
            matched = False
            for real_label, real_id in real_stages.items():
                if any(kw in real_label.lower() for kw in keywords):
                    _stage_ids[logical_name] = real_id
                    matched = True
                    break
            if not matched:
                # Fallback: use the hard-coded ID for this logical stage
                _stage_ids[logical_name] = _FALLBACK_STAGE_MAP.get(logical_name, "5506141375")

        return _pipeline_id

    except httpx.HTTPStatusError as exc:
        # Any HTTP error — fall back to known-good portal values
        print(f"Pipeline fetch failed ({exc.response.status_code}), using hard-coded fallback stage IDs")
        _pipeline_id = "default"
        _stage_ids = _FALLBACK_STAGE_MAP
        return _pipeline_id


async def create_deal_for_contact(
    contact_id: str, lead_name: str, stage_name: str = "Contacted - Pending Call"
) -> str:
    """Create a deal and associate it with a contact. Returns deal ID."""
    pipeline_id = await ensure_pipeline_exists()
    stage_id = _stage_ids.get(stage_name)
    if not stage_id:
        stage_id = list(_stage_ids.values())[0] if _stage_ids else "appointmentscheduled"

    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals"

    # Attempt 1 — full payload with owner + inline association
    payload = {
        "properties": {
            "dealname": f"Lead \u2014 {lead_name}",
            "pipeline": pipeline_id,
            "dealstage": stage_id,
            "hubspot_owner_id": HUBSPOT_SALES_OWNER_ID,
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
            }
        ],
    }
    try:
        resp = await _rate_limited_request("POST", url, json=payload)
        return resp.json()["id"]
    except httpx.HTTPStatusError as exc:
        err = exc.response.text
        print(f"Deal attempt 1 failed ({exc.response.status_code}): {err[:300]}")

    # Attempt 2 — drop owner_id (may be invalid on this portal)
    payload2 = {
        "properties": {
            "dealname": f"Lead \u2014 {lead_name}",
            "pipeline": pipeline_id,
            "dealstage": stage_id,
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
            }
        ],
    }
    try:
        resp = await _rate_limited_request("POST", url, json=payload2)
        return resp.json()["id"]
    except httpx.HTTPStatusError as exc:
        err = exc.response.text
        print(f"Deal attempt 2 failed ({exc.response.status_code}): {err[:300]}")

    # Attempt 3 — bare minimum, associate separately after creation
    payload3 = {
        "properties": {
            "dealname": f"Lead \u2014 {lead_name}",
            "pipeline": pipeline_id,
            "dealstage": stage_id,
        }
    }
    resp = await _rate_limited_request("POST", url, json=payload3)
    deal_id = resp.json()["id"]
    # Associate deal to contact via batch endpoint
    assoc_url = f"{HUBSPOT_API_BASE}/crm/v3/associations/deals/contacts/batch/create"
    try:
        await _rate_limited_request(
            "POST", assoc_url,
            json={"inputs": [{"from": {"id": deal_id}, "to": {"id": contact_id}, "type": "deal_to_contact"}]}
        )
    except Exception as assoc_err:
        print(f"Deal-contact association failed (non-fatal): {assoc_err}")
    return deal_id


async def update_deal_stage(deal_id: str, stage_name: str) -> None:
    """Update a deal's stage."""
    await ensure_pipeline_exists()
    stage_id = _stage_ids.get(stage_name)
    if not stage_id:
        raise ValueError(f"Unknown deal stage: {stage_name}")

    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id}"
    await _rate_limited_request(
        "PATCH", url, json={"properties": {"dealstage": stage_id}}
    )


# ── Task Operations ─────────────────────────────────────────────────────


async def create_task(
    contact_id: str, title: str, owner_id: Optional[str] = None
) -> str:
    """Create a HubSpot task associated with a contact. Returns task ID."""
    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/tasks"
    payload = {
        "properties": {
            "hs_task_subject": title,
            "hs_task_status": "NOT_STARTED",
            "hs_task_priority": "HIGH",
            "hubspot_owner_id": owner_id or HUBSPOT_SALES_OWNER_ID,
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 194,
                    }
                ],
            }
        ],
    }
    resp = await _rate_limited_request("POST", url, json=payload)
    return resp.json()["id"]


# ── Custom Property Setup ──────────────────────────────────────────────

_CUSTOM_CONTACT_PROPERTIES = [
    {
        "name": "lead_property_interest",
        "label": "Property Interest",
        "type": "string",
        "fieldType": "text",
        "groupName": "contactinformation",
        "description": "sale / rental / short-let",
    },
    {
        "name": "lead_budget",
        "label": "Lead Budget",
        "type": "string",
        "fieldType": "text",
        "groupName": "contactinformation",
        "description": "Normalised budget as integer string",
    },
    {
        "name": "lead_preferred_location",
        "label": "Preferred Location",
        "type": "string",
        "fieldType": "text",
        "groupName": "contactinformation",
        "description": "Lead preferred property location",
    },
    {
        "name": "lead_source_channel",
        "label": "Source Channel",
        "type": "string",
        "fieldType": "text",
        "groupName": "contactinformation",
        "description": "Facebook Lead Ad / website / referral",
    },
    {
        "name": "lead_score",
        "label": "Lead Score",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "AI-generated lead quality score 0-100",
    },
    {
        "name": "lead_intent_strength",
        "label": "Intent Strength",
        "type": "string",
        "fieldType": "text",
        "groupName": "contactinformation",
        "description": "high / medium / low",
    },
    {
        "name": "lead_budget_confirmed",
        "label": "Budget Confirmed",
        "type": "enumeration",
        "fieldType": "booleancheckbox",
        "groupName": "contactinformation",
        "description": "Whether the budget was confirmed on the call",
        "options": [
            {"label": "True", "value": "true", "displayOrder": 0},
            {"label": "False", "value": "false", "displayOrder": 1},
        ],
    },
    {
        "name": "lead_timeline",
        "label": "Lead Timeline",
        "type": "string",
        "fieldType": "text",
        "groupName": "contactinformation",
        "description": "Stated move-in or purchase timeline",
    },
    {
        "name": "lead_confidence",
        "label": "Score Confidence",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "Model confidence in the score 0.0-1.0",
    },
    {
        "name": "lead_call_summary",
        "label": "Call Summary",
        "type": "string",
        "fieldType": "textarea",
        "groupName": "contactinformation",
        "description": "AI-generated call summary notes",
    },
]


async def ensure_custom_properties_exist() -> None:
    """Create custom contact properties if they don't already exist."""
    url = f"{HUBSPOT_API_BASE}/crm/v3/properties/contacts"

    try:
        # Fetch existing properties
        resp = await _rate_limited_request("GET", url)
        existing = {p["name"] for p in resp.json().get("results", [])}

        for prop_def in _CUSTOM_CONTACT_PROPERTIES:
            if prop_def["name"] not in existing:
                try:
                    await _rate_limited_request("POST", url, json=prop_def)
                except httpx.HTTPStatusError as exc:
                    # 409 = property already exists (race condition) — safe to ignore
                    if exc.response.status_code != 409:
                        raise
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (403, 401):
            # Log warning, return gracefully
            print("WARNING: Custom property management forbidden. Skipping custom properties creation.")
            return
        raise


async def setup_hubspot() -> None:
    """Run all first-time HubSpot setup: properties + pipeline."""
    await ensure_custom_properties_exist()
    await ensure_pipeline_exists()
