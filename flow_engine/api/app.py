from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from temporalio.client import Client

from flow_engine.api.dependencies import set_temporal_client
from flow_engine.api.routes import execution as execution_router
from flow_engine.api.routes import workflow as workflow_router
from flow_engine.temporal.worker import TEMPORAL_HOST


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = await Client.connect(TEMPORAL_HOST)
    set_temporal_client(client)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Flow Engine API",
        description="Execute n8n-style workflows on Temporal.io",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(workflow_router.router, prefix="/workflows", tags=["workflows"])
    app.include_router(execution_router.router, prefix="/workflows", tags=["executions"])
    return app


app = create_app()
