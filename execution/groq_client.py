"""Groq LLM client — call script generation and transcript analysis."""

import json
from typing import Any

import httpx

from execution.config import GROQ_API_KEY, GROQ_MODEL, CURRENCY_SYMBOL, LOCALE

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}


async def _call_groq(
    messages: list[dict],
    response_format: dict | None = None,
    temperature: float = 0.7,
) -> str:
    """Make a Groq chat completion request. Retry once on 5xx."""
    payload: dict[str, Any] = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }
    if response_format:
        payload["response_format"] = response_format

    for attempt in range(2):
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(_GROQ_URL, headers=_HEADERS, json=payload)
            if resp.status_code >= 500 and attempt == 0:
                import asyncio
                await asyncio.sleep(2)
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    raise RuntimeError("Groq API failed after retry")


async def generate_call_script(lead_data: dict) -> str:
    """
    Generate a personalised outbound call script for a lead.

    lead_data must include: name, interest, location, budget, source.
    """
    first_name = lead_data.get("name", "").split()[0] if lead_data.get("name") else "there"
    budget = lead_data.get("budget_normalised", "")
    budget_display = f"{CURRENCY_SYMBOL} {budget:,}" if isinstance(budget, int) else str(budget)

    prompt = f"""You are a senior real estate sales agent making an outbound call.

Generate a natural, conversational call script for this lead:

- Lead's first name: {first_name}
- Property interest: {lead_data.get('interest', 'property')}
- Preferred location: {lead_data.get('location', 'not specified')}
- Budget: {budget_display}
- Source: {lead_data.get('source', 'website enquiry')}
- Locale: {LOCALE}

The script MUST cover:
1. Warm greeting — reference how they enquired (source channel)
2. Property interest confirmation
3. Budget and timeline qualification
4. Objection handling (just browsing / not ready yet / already working with an agent)
5. Clear close — book a viewing or agree on next step

Keep the tone professional yet warm. Use the lead's first name naturally.
Format as a dialogue script with [AGENT] and [LEAD] markers."""

    return await _call_groq(
        [{"role": "user", "content": prompt}],
        temperature=0.8,
    )


async def analyse_transcript(transcript_text: str) -> dict:
    """
    Analyse a call transcript and return a structured score object.

    Uses JSON mode — never parses free-form text.
    """
    prompt = f"""Analyse this call transcript and return a JSON object with exactly these fields:

- "score": integer 0-100, overall lead quality score
- "intent_strength": string, one of "high", "medium", "low"
- "budget_confirmed": boolean, whether budget was stated and within range
- "timeline": string, stated move-in or purchase timeline
- "objections": array of strings, objections raised on the call
- "summary_notes": string, 2-3 sentence plain-English call summary
- "confidence": float 0-1, your confidence in the score

Scoring rubric (additive, max 100):
- Budget alignment (max 30): Stated budget matches or exceeds the listed price range
- Timeline urgency (max 25): Ready to view within 2 weeks or has a stated move-in date
- Specificity (max 20): Names a specific property type, area, or listed unit
- Engagement quality (max 15): Asked questions, responded positively, did not end call early
- Contact completeness (max 10): Valid phone and email confirmed on the call

Return ONLY the JSON object, no other text.

Transcript:
{transcript_text}"""

    result = await _call_groq(
        [{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return json.loads(result)
