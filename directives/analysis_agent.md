# Analysis Agent — Standard Operating Procedure

## Goal
Analyse VAPI call transcripts using Groq in JSON mode, score leads, update CRM, and dispatch routing.

## Inputs
- Call transcript text from VAPI webhook (`POST /vapi/transcript`)
- Session key from webhook metadata

## Tools / Scripts
- `execution/groq_client.py` — transcript analysis (JSON mode REQUIRED)
- `execution/redis_client.py` — read session, write score
- `execution/hubspot_client.py` — update contact with score fields

## Process
1. Retrieve lead data from Redis using session key.
2. Send transcript to Groq with JSON mode (`response_format: {"type": "json_object"}`).
3. Extract score object with fields: score, intent_strength, budget_confirmed, timeline, objections, summary_notes, confidence.
4. If confidence < 0.6: create a manual review task in HubSpot.
5. Write score object to Redis.
6. Update HubSpot contact with all scored fields.
7. Dispatch Lead Router.

## Scoring Rubric (Additive, Max 100)
| Dimension | Signal | Max Points |
|-----------|--------|------------|
| Budget alignment | Budget matches/exceeds listed price | 30 |
| Timeline urgency | Ready to view within 2 weeks | 25 |
| Specificity | Names specific type, area, or unit | 20 |
| Engagement quality | Positive responses, asked questions | 15 |
| Contact completeness | Phone + email confirmed on call | 10 |

## Edge Cases
- Missing session in Redis: raise error → Monitor Agent handles.
- Groq returns malformed JSON: caught by json.loads() → Monitor Agent.
- Low confidence (< 0.6): flag for manual review but still route.

## Outputs
- Score object in Redis
- HubSpot contact updated with score fields
- Lead Router dispatched
