# Intake Agent — Standard Operating Procedure

## Goal
Capture, validate, and normalise incoming lead submissions, then create or update CRM records and dispatch the Call Agent.

## Inputs
- Raw lead payload from `POST /lead/inbound` webhook
- Required fields: `name`, `phone`
- Optional fields: `email`, `interest`, `budget`, `location`, `source`

## Tools / Scripts
- `execution/phone_normalizer.py` — normalise phone to E.164
- `execution/qa_checks.py` — validate payload, email, budget
- `execution/hubspot_client.py` — CRM create/update
- `execution/redis_client.py` — session storage

## Process
1. Validate required fields (name + phone). Reject and log if missing.
2. Normalise phone number using `phonenumbers` with `PHONE_DEFAULT_COUNTRY` fallback.
3. Validate email format (RFC 5322). Flag invalid but don't reject.
4. Normalise budget to plain integer (strip symbols, commas, shorthand).
5. Deduplicate: search HubSpot by E.164 phone, then by email.
6. If contact exists: update with latest data. If not: create new contact.
7. Create a deal with stage "Contacted - Pending Call".
8. Store lead session in Redis (key: `lead:{e164}:{timestamp}`, TTL: 24h).
9. Dispatch Call Agent with enriched lead data.

## Edge Cases
- Phone numbers with no country code: handled by `PHONE_DEFAULT_COUNTRY` env var.
- Duplicate contacts: always prefer phone match over email match.
- Budget shorthand: "1.5m" → 1500000, "500k" → 500000, "NGN 50,000,000" → 50000000.
- Missing email: proceed without email — do not block pipeline.

## Outputs
- HubSpot contact ID written to Redis session
- HubSpot deal ID written to Redis session
- Call Agent dispatched
