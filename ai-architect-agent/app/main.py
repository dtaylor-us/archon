import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.agent import router as agent_router

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Architect Agent starting up")
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
