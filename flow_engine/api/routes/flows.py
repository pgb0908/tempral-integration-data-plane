from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from flow_engine.api.dependencies import get_flow_store
from flow_engine.models.flow import FlowDeployment
from flow_engine.parser.workflow_parser import WorkflowParser
from flow_engine.store.flow_store import FlowStore

from datetime import datetime, timezone

router = APIRouter()


class DeployRequest(BaseModel):
    name: str
    workflow_definition: dict[str, Any]


class UpdateRequest(BaseModel):
    workflow_definition: dict[str, Any]
    name: str | None = None


@router.post("", response_model=FlowDeployment, status_code=201)
async def deploy_flow(
    body: DeployRequest,
    store: FlowStore = Depends(get_flow_store),
) -> FlowDeployment:
    try:
        WorkflowParser.parse(body.workflow_definition)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid workflow definition: {exc}") from exc

    now = datetime.now(timezone.utc)
    flow_id = "flow-" + uuid4().hex[:8]
    deployment = FlowDeployment(
        flow_id=flow_id,
        name=body.name,
        workflow_definition=body.workflow_definition,
        version=1,
        created_at=now,
        updated_at=now,
    )
    store.save(deployment)
    return deployment


@router.get("", response_model=list[FlowDeployment])
async def list_flows(store: FlowStore = Depends(get_flow_store)) -> list[FlowDeployment]:
    return store.list()


@router.get("/{flow_id}", response_model=FlowDeployment)
async def get_flow(
    flow_id: str,
    store: FlowStore = Depends(get_flow_store),
) -> FlowDeployment:
    deployment = store.get(flow_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
    return deployment


@router.put("/{flow_id}", response_model=FlowDeployment)
async def update_flow(
    flow_id: str,
    body: UpdateRequest,
    store: FlowStore = Depends(get_flow_store),
) -> FlowDeployment:
    try:
        WorkflowParser.parse(body.workflow_definition)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid workflow definition: {exc}") from exc

    try:
        return store.update(flow_id, body.workflow_definition, body.name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")


@router.delete("/{flow_id}", status_code=204)
async def delete_flow(
    flow_id: str,
    store: FlowStore = Depends(get_flow_store),
) -> None:
    if not store.delete(flow_id):
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
