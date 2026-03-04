"""
Tests for the Deploy/Run API (no Temporal server required).

Uses FastAPI TestClient with a temp FlowStore directory and a mocked Temporal client.
"""
from __future__ import annotations

import json
import pathlib
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from flow_engine.api import dependencies
from flow_engine.api.routes import flows as flows_router
from flow_engine.api.routes import runs as runs_router
from flow_engine.store.flow_store import FlowStore

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "sample_workflow.json"


@pytest.fixture()
def workflow_definition():
    return json.loads(FIXTURE.read_text())


@pytest.fixture()
def client(tmp_path, workflow_definition):
    """Create app with isolated FlowStore and mocked Temporal client."""
    store = FlowStore(store_dir=tmp_path / "flows")
    dependencies.set_flow_store(store)

    mock_client = MagicMock()
    mock_client.start_workflow = AsyncMock()
    mock_client.get_workflow_handle = MagicMock()
    dependencies.set_temporal_client(mock_client)

    @asynccontextmanager
    async def noop_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    app = FastAPI(lifespan=noop_lifespan)
    app.include_router(flows_router.router, prefix="/flows", tags=["flows"])
    app.include_router(runs_router.router, tags=["runs"])

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Deploy (POST /flows)
# ---------------------------------------------------------------------------

def test_deploy_flow(client, workflow_definition):
    resp = client.post("/flows", json={"name": "my-flow", "workflow_definition": workflow_definition})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "my-flow"
    assert data["flow_id"].startswith("flow-")
    assert data["version"] == 1


def test_list_flows_empty(client):
    resp = client.get("/flows")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_flows_after_deploy(client, workflow_definition):
    client.post("/flows", json={"name": "f1", "workflow_definition": workflow_definition})
    client.post("/flows", json={"name": "f2", "workflow_definition": workflow_definition})
    resp = client.get("/flows")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_flow(client, workflow_definition):
    deploy_resp = client.post("/flows", json={"name": "test", "workflow_definition": workflow_definition})
    flow_id = deploy_resp.json()["flow_id"]
    resp = client.get(f"/flows/{flow_id}")
    assert resp.status_code == 200
    assert resp.json()["flow_id"] == flow_id


def test_get_flow_not_found(client):
    resp = client.get("/flows/flow-nonexistent")
    assert resp.status_code == 404


def test_update_flow(client, workflow_definition):
    deploy_resp = client.post("/flows", json={"name": "test", "workflow_definition": workflow_definition})
    flow_id = deploy_resp.json()["flow_id"]

    resp = client.put(f"/flows/{flow_id}", json={"workflow_definition": workflow_definition, "name": "updated"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == 2
    assert data["name"] == "updated"


def test_update_flow_not_found(client, workflow_definition):
    resp = client.put("/flows/flow-ghost", json={"workflow_definition": workflow_definition})
    assert resp.status_code == 404


def test_delete_flow(client, workflow_definition):
    deploy_resp = client.post("/flows", json={"name": "del", "workflow_definition": workflow_definition})
    flow_id = deploy_resp.json()["flow_id"]

    resp = client.delete(f"/flows/{flow_id}")
    assert resp.status_code == 204

    assert client.get(f"/flows/{flow_id}").status_code == 404


def test_delete_flow_not_found(client):
    resp = client.delete("/flows/flow-ghost")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Run (POST /flows/{flow_id}/runs)
# ---------------------------------------------------------------------------

def test_start_run(client, workflow_definition):
    deploy_resp = client.post("/flows", json={"name": "run-test", "workflow_definition": workflow_definition})
    flow_id = deploy_resp.json()["flow_id"]

    resp = client.post(f"/flows/{flow_id}/runs", json={"initial_data": [{"name": "World"}]})
    assert resp.status_code == 202
    data = resp.json()
    assert data["flow_id"] == flow_id
    assert data["run_id"].startswith("run-")
    assert data["status"] == "started"


def test_start_run_custom_run_id(client, workflow_definition):
    deploy_resp = client.post("/flows", json={"name": "run-test", "workflow_definition": workflow_definition})
    flow_id = deploy_resp.json()["flow_id"]

    resp = client.post(f"/flows/{flow_id}/runs", json={"run_id": "my-custom-run"})
    assert resp.status_code == 202
    assert resp.json()["run_id"] == "my-custom-run"


def test_start_run_flow_not_found(client):
    resp = client.post("/flows/flow-ghost/runs", json={})
    assert resp.status_code == 404
