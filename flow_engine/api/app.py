from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from temporalio.client import Client

from flow_engine.api.dependencies import set_flow_store, set_temporal_client
from flow_engine.api.routes import flows as flows_router
from flow_engine.api.routes import runs as runs_router
from flow_engine.store.flow_store import FlowStore
from flow_engine.temporal.worker import TEMPORAL_HOST


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = await Client.connect(TEMPORAL_HOST)
    set_temporal_client(client)
    set_flow_store(FlowStore())
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Flow Engine API",
        description="Deploy and run n8n-style workflows on Temporal.io",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.include_router(flows_router.router, prefix="/flows", tags=["flows"])
    app.include_router(runs_router.router, tags=["runs"])
    return app


app = create_app()
