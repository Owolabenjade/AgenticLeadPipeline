# Call Agent — Standard Operating Procedure

## Goal
Generate a personalised outbound call script and trigger an AI-powered call via VAPI.

## Inputs
- Enriched lead data from Redis session
- Session key for callback metadata

## Tools / Scripts
- `execution/groq_client.py` — call script generation (llama-3.3-70b-versatile)
- `execution/vapi_client.py` — outbound call triggering
- `execution/redis_client.py` — set call_pending flag

## Process
1. Read lead data from Redis using session key.
2. Generate personalised call script via Groq. Script must include:
   - Lead's first name
   - Property type and location of interest
   - Budget (formatted with CURRENCY_SYMBOL)
   - Source channel reference
3. Script must cover: greeting, property confirmation, budget/timeline qualification, objection handling, and close.
4. Trigger outbound call via VAPI with the script and webhook callback URL.
5. On HTTP 201: set `call_pending` flag in Redis (2h TTL).
6. On failure: retry once after 5 seconds. If still failing, log to Monitor Agent and skip call stage.

## Edge Cases
- VAPI timeout: retry once, then skip. Pipeline must not block on call failures.
- Very long scripts: VAPI first message is truncated to 500 chars; full script goes into system prompt.
- Invalid phone format: should never reach this agent (caught by Intake Agent).

## Outputs
- VAPI call initiated (call ID stored in lead data)
- `call_pending` flag set in Redis
- On failure: error logged, pipeline continues to nurture path
