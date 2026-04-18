import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.agent import router as agent_router
from app.llm.client import LLMClient
from app.memory.store import MemoryStore
from app.pipeline import compile_pipeline, init_registry
from app.tools.registry import build_registry

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Architect Agent starting up")

    # Initialise shared LLM client
    llm_client = LLMClient()
    app.state.llm_client = llm_client
    logger.info("LLMClient attached to app.state")

    # Initialise Qdrant-backed memory store
    memory_store = MemoryStore()
    await memory_store._ensure_collection()
    app.state.memory_store = memory_store
    logger.info("MemoryStore attached to app.state")

    # Build tool registry and wire it into pipeline nodes
    registry = build_registry(llm_client, memory_store)
    app.state.tool_registry = registry
    init_registry(registry)
    logger.info("Tool registry initialised with %d tools", len(registry))

    # Compile the LangGraph pipeline graph
    compile_pipeline()

    yield
    logger.info("AI Architect Agent shutting down")


app = FastAPI(
    title="AI Architect Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(agent_router)


@app.get("/health")
async def health():
    return JSONResponse({"status": "UP",
                         "service": "ai-architect-agent"})
