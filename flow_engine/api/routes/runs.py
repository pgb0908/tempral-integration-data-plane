from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from temporalio.service import RPCError

from flow_engine.api.dependencies import get_flow_store, get_temporal_client
from flow_engine.store.flow_store import FlowStore
from flow_engine.temporal.worker import TASK_QUEUE
from flow_engine.temporal.workflow import FlowWorkflow

router = APIRouter()


class RunRequest(BaseModel):
    initial_data: list[dict[str, Any]] = []
    run_id: str | None = None


class RunResponse(BaseModel):
    flow_id: str
    run_id: str
    status: str = "started"


async def _get_handle(run_id: str):
    client = get_temporal_client()
    return client.get_workflow_handle(run_id)


@router.post("/flows/{flow_id}/runs", response_model=RunResponse, status_code=202)
async def start_run(
    flow_id: str,
    body: RunRequest,
    store: FlowStore = Depends(get_flow_store),
) -> RunResponse:
    deployment = store.get(flow_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")

    run_id = body.run_id or ("run-" + uuid4().hex[:8])
    client = get_temporal_client()

    await client.start_workflow(
        FlowWorkflow.run,
        args=[
            {
                "workflow_definition": deployment.workflow_definition,
                "initial_data": body.initial_data,
            }
        ],
        id=run_id,
        task_queue=TASK_QUEUE,
    )

    return RunResponse(flow_id=flow_id, run_id=run_id)


@router.get("/runs/{run_id}/status")
async def get_run_status(run_id: str) -> dict[str, Any]:
    handle = await _get_handle(run_id)
    try:
        status = await handle.query(FlowWorkflow.get_status)
        return {"run_id": run_id, **status}
    except RPCError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runs/{run_id}/result")
async def get_run_result(run_id: str) -> dict[str, Any]:
    handle = await _get_handle(run_id)
    try:
        result = await handle.result()
        return {"run_id": run_id, "result": result}
    except RPCError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str) -> dict[str, str]:
    handle = await _get_handle(run_id)
    try:
        await handle.signal(FlowWorkflow.cancel_workflow)
        return {"run_id": run_id, "status": "cancel_requested"}
    except RPCError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
