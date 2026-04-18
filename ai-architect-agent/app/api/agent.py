import asyncio
import logging
import os
from typing import AsyncGenerator

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models import ArchitectureContext, PipelineMode, HistoryMessage

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentStreamRequest(BaseModel):
    conversationId: str
    userMessage: str
    mode: str = "AUTO"
    history: list[dict] = []
    context: dict | None = None


class AgentResponseChunk(BaseModel):
    type: str
    content: str | None = None
    stage: str | None = None
    toolName: str | None = None
    payload: dict | None = None
    conversationId: str | None = None
    metadata: dict | None = None


def chunk(event_type: str, **kwargs) -> str:
    data = AgentResponseChunk(type=event_type, **kwargs)
    return data.model_dump_json(exclude_none=True) + "\n"


async def run_stub_pipeline(
    ctx: ArchitectureContext,
) -> AsyncGenerator[str, None]:
    stages = [
        ("requirement_parsing",      "Parsing requirements..."),
        ("requirement_challenge",    "Challenging requirements and identifying gaps..."),
        ("scenario_modeling",        "Modeling small / medium / large scenarios..."),
        ("characteristic_inference", "Inferring architecture characteristics..."),
        ("conflict_analysis",        "Analyzing characteristic conflicts..."),
        ("architecture_generation",  "Generating architecture design..."),
        ("trade_off_analysis",       "Running trade-off analysis..."),
        ("adl_generation",           "Generating ADL rules..."),
        ("weakness_analysis",        "Analyzing architectural weaknesses..."),
        ("fmea_analysis",            "Running FMEA+ risk analysis..."),
        ("architecture_review",      "Running architect review pass..."),
    ]

    for stage_name, stage_desc in stages:
        yield chunk("STAGE_START", stage=stage_name)
        await asyncio.sleep(0.3)

        for word in stage_desc.split():
            yield chunk("CHUNK", content=word + " ", stage=stage_name)
            await asyncio.sleep(0.05)

        yield chunk("STAGE_COMPLETE", stage=stage_name,
                    payload={"status": "stub_complete",
                             "stage": stage_name})
        await asyncio.sleep(0.1)

    yield chunk(
        "COMPLETE",
        conversationId=ctx.conversation_id,
        payload={
            "message": "Phase 1 stub: full pipeline streamed successfully.",
            "stages_executed": len(stages),
            "iteration": ctx.iteration,
        },
    )


@router.post("/agent/stream")
async def agent_stream(
    request: AgentStreamRequest,
    x_internal_secret: str = Header(
        default=None, alias="x-internal-secret"),
):
    expected = os.getenv("INTERNAL_SECRET", "dev-secret-change-in-prod")
    if x_internal_secret != expected:
        raise HTTPException(status_code=401,
                            detail="Invalid internal secret")

    logger.info("Agent stream request conversation=%s mode=%s",
                request.conversationId, request.mode)

    ctx = ArchitectureContext(
        conversation_id=request.conversationId,
        raw_requirements=request.userMessage,
        mode=(PipelineMode(request.mode)
              if request.mode in PipelineMode.__members__
              else PipelineMode.AUTO),
        history=[
            HistoryMessage(
                id=str(i),
                role=h.get("role", "USER"),
                content=h.get("content", ""),
            )
            for i, h in enumerate(request.history)
        ],
    )

    return StreamingResponse(
        run_stub_pipeline(ctx),
        media_type="application/x-ndjson",
        headers={"X-Conversation-Id": ctx.conversation_id},
    )
