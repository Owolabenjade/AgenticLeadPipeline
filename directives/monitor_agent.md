# Monitor Agent — Standard Operating Procedure

## Goal
Wrap all agent executions in error handling. On failure: log, alert, and exit gracefully.

## Inputs
- Decorated agent function
- Agent name, session key, lead context

## Tools / Scripts
- `execution/monitor_agent.py` — `@monitor` decorator
- `execution/redis_client.py` — error record storage
- `execution/slack_client.py` — #system-alerts webhook
- `logs/failed_leads.jsonl` — local error log

## Process
On any unhandled exception in a monitored agent:
1. Extract: agent name, session ID, error type, stack trace (last 500 chars).
2. Write error record to Redis: key `error:{session_id}:{timestamp}`.
3. Post alert to #system-alerts Slack channel within 30 seconds.
4. Alert must include: agent name, lead name, masked phone (last 4 digits), error type, suggested fix.
5. Append error record to `logs/failed_leads.jsonl`.
6. Do NOT re-raise — return None and exit gracefully.

## Key Rules
- Never re-raise exceptions from the decorator — leads must be manually recoverable.
- Slack alerts are best-effort: if Slack fails, log locally and continue.
- Redis writes are best-effort: if Redis fails, log locally and continue.
- Phone numbers in alerts must be masked (show only last 4 digits).

## Outputs
- Error record in Redis
- Slack #system-alerts notification
- Error appended to `logs/failed_leads.jsonl`
- Agent returns None instead of crashing
