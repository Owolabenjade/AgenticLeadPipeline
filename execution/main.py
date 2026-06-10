"""FastAPI application — webhook endpoints + dashboard frontend for the lead pipeline."""

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from execution import hubspot_client
from execution.intake_agent import process_lead
from execution.analysis_agent import process_transcript

# ── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("main")

# ── Simple credential store (replace with real auth in production) ───────
_ADMIN_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
_ADMIN_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")
_VALID_TOKENS: dict[str, dict] = {}   # token → user info

_BEARER = HTTPBearer(auto_error=False)


# ── Lifespan — run HubSpot setup on startup ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run first-time setup on startup."""
    logger.info("Running HubSpot first-time setup…")
    try:
        await hubspot_client.setup_hubspot()
        logger.info("HubSpot setup complete.")
    except Exception as exc:
        logger.error("HubSpot setup failed (non-fatal): %s", exc)
    yield


app = FastAPI(
    title="AI Agentic Lead Pipeline",
    version="1.0.0",
    description="Multi-agent lead conversion pipeline — capture, call, score, route.",
    lifespan=lifespan,
)

# ── Static files + SPA root ──────────────────────────────────────────────
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")


# ── Request / Response Models ────────────────────────────────────────────

class LeadPayload(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    interest: Optional[str] = ""
    budget: Optional[str] = ""
    location: Optional[str] = ""
    source: Optional[str] = "website"


class LoginPayload(BaseModel):
    username: str
    password: str


class ActionPayload(BaseModel):
    action: str          # "recall" | "nurture" | "hubspot"
    session_key: str


# ── Auth helper ──────────────────────────────────────────────────────────

def _require_auth(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_BEARER),
) -> dict:
    """Validate Bearer token; raise 401 on failure."""
    if not creds or creds.credentials not in _VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )
    return _VALID_TOKENS[creds.credentials]


# ════════════════════════════════════════════════════════════════════════
# FRONTEND ENDPOINTS
# ════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_spa():
    """Serve the SPA shell."""
    html_path = _FRONTEND_DIR / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Frontend not found</h1>", status_code=404)
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.post("/api/login")
async def api_login(payload: LoginPayload):
    """Authenticate and return a session token."""
    if payload.username != _ADMIN_USERNAME or payload.password != _ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = f"tok-{payload.username}-{int(time.time())}"
    _VALID_TOKENS[token] = {
        "username": payload.username,
        "role": "Administrator",
    }
    return {"token": token, "username": payload.username, "role": "Administrator"}


@app.get("/api/leads")
async def api_leads(user: dict = Depends(_require_auth)):
    """
    Return all active lead sessions from Redis.
    Falls back to an empty list if Redis is unavailable.
    """
    try:
        from execution import redis_client
        result = await redis_client._execute(["KEYS", "lead:*"])
        keys = result or []
        leads = []
        for key in keys[:100]:  # cap at 100 for safety
            try:
                data = await redis_client.get_lead_session(key)
                if data:
                    data["session_key"] = key
                    # Fetch score if available
                    try:
                        score_raw = await redis_client._execute(["GET", f"score:{key}"])
                        if score_raw:
                            score_obj = json.loads(score_raw)
                            data["score_obj"] = score_obj
                            data["score"] = score_obj.get("score", 0)
                    except Exception:
                        pass
                    leads.append(data)
            except Exception:
                pass
        return JSONResponse(content=leads)
    except Exception as exc:
        logger.warning("Redis unavailable for /api/leads: %s", exc)
        return JSONResponse(content=[])


@app.get("/api/stats")
async def api_stats(user: dict = Depends(_require_auth)):
    """
    Compile pipeline metrics from Redis.
    Falls back to zeros if Redis is unavailable.
    """
    try:
        from execution import redis_client
        lead_keys  = await redis_client._execute(["KEYS", "lead:*"])  or []
        score_keys = await redis_client._execute(["KEYS", "score:*"]) or []
        error_keys = await redis_client._execute(["KEYS", "error:*"]) or []

        total  = len(lead_keys)
        scored = len(score_keys)
        errors = len(error_keys)

        scores = []
        for sk in score_keys[:50]:
            try:
                raw = await redis_client._execute(["GET", sk])
                if raw:
                    obj = json.loads(raw)
                    s   = obj.get("score", 0)
                    if isinstance(s, (int, float)):
                        scores.append(int(s))
            except Exception:
                pass

        hot  = sum(1 for s in scores if s >= 65)
        warm = sum(1 for s in scores if 40 <= s < 65)
        cold = sum(1 for s in scores if s < 40)
        avg  = round(sum(scores) / len(scores), 1) if scores else 0

        return JSONResponse(content={
            "total_leads":       total,
            "hot_leads":         hot,
            "warm_leads":        warm,
            "cold_leads":        cold,
            "calls_made":        scored,
            "errors":            errors,
            "avg_score":         avg,
            "call_success_rate": round(scored / total * 100) if total else 0,
            "conversion_rate":   round(hot    / total * 100) if total else 0,
        })
    except Exception as exc:
        logger.warning("Redis unavailable for /api/stats: %s", exc)
        return JSONResponse(content={
            "total_leads": 0, "hot_leads": 0, "calls_made": 0,
            "avg_score": 0, "call_success_rate": 0, "conversion_rate": 0,
        })


@app.get("/api/alerts")
async def api_alerts(user: dict = Depends(_require_auth)):
    """
    Retrieve recent error / alert records from Redis.
    Also reads the failed_leads.jsonl log file.
    """
    alerts = []

    # 1. Read from Redis error keys
    try:
        from execution import redis_client
        error_keys = await redis_client._execute(["KEYS", "error:*"]) or []
        for ek in sorted(error_keys, reverse=True)[:20]:
            try:
                raw = await redis_client._execute(["GET", ek])
                if raw:
                    rec = json.loads(raw)
                    rec["type"]     = "error"
                    rec["type_cls"] = "red"
                    rec["id"]       = ek
                    alerts.append(rec)
            except Exception:
                pass
    except Exception as exc:
        logger.warning("Redis unavailable for /api/alerts: %s", exc)

    # 2. Read from failed_leads.jsonl
    log_path = Path(__file__).resolve().parent.parent / "logs" / "failed_leads.jsonl"
    if log_path.exists():
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines[-20:]):
                try:
                    rec = json.loads(line)
                    rec["type"]     = "error"
                    rec["type_cls"] = "red"
                    rec["id"]       = rec.get("session_key", "")
                    if rec not in alerts:
                        alerts.append(rec)
                except Exception:
                    pass
        except Exception:
            pass

    alerts.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return JSONResponse(content=alerts[:30])


@app.post("/api/leads/action")
async def api_lead_action(
    payload: ActionPayload,
    background_tasks: BackgroundTasks,
    user: dict = Depends(_require_auth),
):
    """
    Trigger a manual action on a lead:
    - recall   → re-dispatch VAPI outbound call
    - nurture  → re-send Brevo nurture email
    - hubspot  → (client-side redirect; server acknowledges)
    """
    action      = payload.action
    session_key = payload.session_key

    if action not in ("recall", "nurture", "hubspot"):
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    if action == "hubspot":
        return JSONResponse(content={"status": "ok", "action": action})

    try:
        from execution import redis_client
        lead_data = await redis_client.get_lead_session(session_key)
    except Exception:
        lead_data = None

    if not lead_data:
        raise HTTPException(status_code=404, detail="Lead session not found")

    if action == "recall":
        from execution.call_agent import dispatch_call_agent
        background_tasks.add_task(
            dispatch_call_agent,
            lead_data,
            session_key=session_key,
        )
        return JSONResponse(content={"status": "dispatched", "action": "recall"})

    if action == "nurture":
        score_obj = lead_data.get("score", {})
        from execution.nurture_agent import dispatch_nurture_agent
        background_tasks.add_task(
            dispatch_nurture_agent,
            lead_data,
            score_obj,
            requeue_ttl=172_800,
            session_key=session_key,
        )
        return JSONResponse(content={"status": "dispatched", "action": "nurture"})


# ════════════════════════════════════════════════════════════════════════
# EXISTING PIPELINE WEBHOOKS
# ════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-lead-pipeline"}


@app.post("/lead/inbound")
async def inbound_lead(
    payload: LeadPayload,
    background_tasks: BackgroundTasks,
):
    """
    Receive a lead submission, validate, and dispatch the pipeline.
    Required: name, phone.
    """
    logger.info("Received inbound lead: %s / %s", payload.name, payload.phone)
    background_tasks.add_task(
        process_lead,
        payload.model_dump(),
        session_key="",
        lead_name=payload.name,
        lead_phone=payload.phone,
    )
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "message": f"Lead '{payload.name}' accepted for processing.",
        },
    )


@app.post("/vapi/transcript")
async def vapi_transcript_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Receive a VAPI call transcript webhook and dispatch the Analysis Agent."""
    body = await request.json()
    message     = body.get("message", {})
    transcript  = message.get("transcript", "") or body.get("transcript", "")
    metadata    = message.get("metadata", {}) or body.get("metadata", {})
    session_key = metadata.get("session_key", "")
    call_data   = message.get("call", {}) or body.get("call", {})

    if not transcript:
        logger.warning("VAPI webhook received with no transcript")
        return JSONResponse(status_code=200, content={"status": "skipped", "reason": "no transcript"})

    if not session_key:
        logger.warning("VAPI webhook received with no session_key in metadata")
        return JSONResponse(status_code=200, content={"status": "skipped", "reason": "no session_key"})

    logger.info("Received VAPI transcript for session %s (%d chars)", session_key, len(transcript))

    background_tasks.add_task(
        process_transcript,
        transcript,
        session_key,
        lead_name="",
        lead_phone="",
    )
    return JSONResponse(status_code=200, content={"status": "processing", "session_key": session_key})
