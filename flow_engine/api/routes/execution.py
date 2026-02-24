from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from temporalio.service import RPCError

from flow_engine.api.dependencies import get_temporal_client
from flow_engine.temporal.workflow import FlowWorkflow

router = APIRouter()


async def _get_handle(workflow_id: str):
    client = get_temporal_client()
    return client.get_workflow_handle(workflow_id)


@router.get("/{workflow_id}/status")
async def get_status(workflow_id: str) -> dict[str, Any]:
    handle = await _get_handle(workflow_id)
    try:
        status = await handle.query(FlowWorkflow.get_status)
        return {"workflow_id": workflow_id, **status}
    except RPCError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workflow_id}/result")
async def get_result(workflow_id: str) -> dict[str, Any]:
    handle = await _get_handle(workflow_id)
    try:
        result = await handle.result()
        return {"workflow_id": workflow_id, "result": result}
    except RPCError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str) -> dict[str, str]:
    handle = await _get_handle(workflow_id)
    try:
        await handle.signal(FlowWorkflow.cancel_workflow)
        return {"workflow_id": workflow_id, "status": "cancel_requested"}
    except RPCError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
