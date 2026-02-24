from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from flow_engine.api.dependencies import get_temporal_client
from flow_engine.parser.workflow_parser import WorkflowParser
from flow_engine.temporal.worker import TASK_QUEUE
from flow_engine.temporal.workflow import FlowWorkflow

router = APIRouter()


class ExecuteRequest(BaseModel):
    workflow_definition: dict[str, Any]
    initial_data: list[dict[str, Any]] = []
    workflow_id: str | None = None


class ExecuteResponse(BaseModel):
    workflow_id: str
    status: str = "started"


@router.post("/execute", response_model=ExecuteResponse)
async def execute_workflow(body: ExecuteRequest) -> ExecuteResponse:
    # Validate the workflow definition early
    try:
        WorkflowParser.parse(body.workflow_definition)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid workflow definition: {exc}") from exc

    workflow_id = body.workflow_id or f"flow-{uuid.uuid4()}"
    client = get_temporal_client()

    await client.start_workflow(
        FlowWorkflow.run,
        args=[
            {
                "workflow_definition": body.workflow_definition,
                "initial_data": body.initial_data,
            }
        ],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    return ExecuteResponse(workflow_id=workflow_id)
