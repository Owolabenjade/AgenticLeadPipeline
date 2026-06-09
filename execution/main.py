"""FastAPI application — webhook endpoints for the lead pipeline."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from execution import hubspot_client
from execution.intake_agent import process_lead
from execution.analysis_agent import process_transcript

# ── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("main")


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


# ── Request Models ──────────────────────────────────────────────────────

class LeadPayload(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    interest: Optional[str] = ""
    budget: Optional[str] = ""
    location: Optional[str] = ""
    source: Optional[str] = "website"


# ── Endpoints ───────────────────────────────────────────────────────────

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

    # Dispatch full pipeline in the background so the webhook returns fast
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
    """
    Receive a VAPI call transcript webhook and dispatch the Analysis Agent.
    """
    body = await request.json()

    # VAPI webhook payload structure
    message = body.get("message", {})
    transcript = message.get("transcript", "") or body.get("transcript", "")
    metadata = message.get("metadata", {}) or body.get("metadata", {})
    session_key = metadata.get("session_key", "")
    call_data = message.get("call", {}) or body.get("call", {})

    if not transcript:
        logger.warning("VAPI webhook received with no transcript")
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": "no transcript"},
        )

    if not session_key:
        logger.warning("VAPI webhook received with no session_key in metadata")
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": "no session_key"},
        )

    logger.info(
        "Received VAPI transcript for session %s (%d chars)",
        session_key, len(transcript),
    )

    # Dispatch Analysis Agent in background
    background_tasks.add_task(
        process_transcript,
        transcript,
        session_key,
        lead_name="",
        lead_phone="",
    )

    return JSONResponse(
        status_code=200,
        content={"status": "processing", "session_key": session_key},
    )
