# Closing Agent — Standard Operating Procedure

## Goal
Handle qualified (hot) leads: generate a brief, alert sales team via Slack, create CRM follow-up task.

## Inputs
- Lead data with score object (score >= 65)
- Session key

## Tools / Scripts
- `execution/closing_agent.py` — brief generation + Slack posting
- `templates/lead_brief.jinja2` — Slack brief template
- `execution/hubspot_client.py` — task creation
- `execution/slack_client.py` — #hot-leads webhook

## Process
1. Render lead brief from `templates/lead_brief.jinja2` with lead data and score.
2. Post formatted brief to #hot-leads Slack channel.
3. Tag SLACK_SALES_HEAD_ID in the message body.
4. Deal stage should already be "Sales Qualified" (set by router).
5. Create HubSpot task: "Call within 2 hours" assigned to HUBSPOT_SALES_OWNER_ID.

## Brief Must Include
- Contact details (name, phone, email)
- Property interest, location, budget (with CURRENCY_SYMBOL)
- Lead score and confidence
- Timeline
- Call summary
- Objections raised
- Recommended next action

## Outputs
- Slack #hot-leads message posted with sales head tagged
- HubSpot follow-up task created
