# Routing Agent — Standard Operating Procedure

## Goal
Route scored leads to the appropriate downstream agent based on score ranges.

## Inputs
- Lead data with score object from Analysis Agent
- Session key

## Tools / Scripts
- `execution/lead_router.py` — routing logic
- `execution/hubspot_client.py` — deal stage updates

## Routing Rules
| Score Range | Action | HubSpot Deal Stage |
|-------------|--------|--------------------|
| 65 – 100 | Dispatch Closing Agent | Sales Qualified |
| 40 – 64 | Dispatch Nurture Agent (48h re-queue) | Nurturing |
| 0 – 39 | Dispatch Nurture Agent (7d re-queue) | Long-term Nurture |

## Process
1. Read score from score object.
2. Update HubSpot deal stage based on score range.
3. Dispatch appropriate downstream agent.

## Edge Cases
- Non-numeric score: default to 0 (cold lead path).
- Missing deal ID: skip deal stage update, still route the lead.

## Outputs
- HubSpot deal stage updated
- Downstream agent dispatched
