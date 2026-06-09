# Nurture Agent — Standard Operating Procedure

## Goal
Follow up with unqualified and warm leads via email and re-queue them for future contact.

## Inputs
- Lead data with score object (score < 65)
- Re-queue TTL (48 hours for score 40-64, 7 days for score 0-39)
- Session key

## Tools / Scripts
- `execution/nurture_agent.py` — email dispatch + re-queue
- `templates/nurture_email.jinja2` — HTML email template
- `execution/brevo_client.py` — transactional email via Brevo
- `execution/redis_client.py` — nurture re-queue

## Process
1. Render nurture email from `templates/nurture_email.jinja2`.
2. Subject line must reference lead's property interest and location.
3. Send email via Brevo transactional API.
4. If call duration > 30 seconds: also trigger a voicemail via VAPI (future enhancement).
5. Add lead to Redis re-queue with appropriate TTL.
6. Deal stage should already be set by router.

## Edge Cases
- No email address: skip email, still re-queue in Redis.
- Brevo rate limit (300/day free tier): log warning, re-queue for retry.
- Invalid email: skip email send (caught by QA checks).

## Outputs
- Nurture email sent (or skipped if no email)
- Lead re-queued in Redis with TTL
