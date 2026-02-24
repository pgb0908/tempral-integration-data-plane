"""
End-to-end unit test for the n8n sample workflow (no Temporal server required).
Runs: ManualTrigger → Set → HttpRequest (mocked)
"""
from __future__ import annotations

import json
import pathlib

import pytest

from flow_engine.models.execution import ExecutionContext, NodeResult, NodeStatus
from flow_engine.nodes.set_node import SetNodeExecutor
from flow_engine.nodes.trigger import ManualTriggerExecutor
from flow_engine.parser.graph_builder import WorkflowGraph
from flow_engine.parser.workflow_parser import WorkflowParser

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "n8n_sample.json"


@pytest.fixture
def workflow_def():
    return WorkflowParser.parse(json.loads(FIXTURE.read_text()))


@pytest.fixture
def ctx():
    return ExecutionContext(
        workflow_id="test-wf",
        run_id="test-run",
        initial_data=[{}],
    )


def test_parse_n8n_sample(workflow_def):
    assert len(workflow_def.nodes) == 3
    names = [n.name for n in workflow_def.nodes]
    assert "When clicking 'Execute Workflow'" in names
    assert "Set User Data" in names
    assert "Call External API" in names


def test_topo_order(workflow_def):
    graph = WorkflowGraph(workflow_def)
    order = graph.topological_sort()
    assert order[0] == "When clicking 'Execute Workflow'"
    assert order[1] == "Set User Data"
    assert order[2] == "Call External API"


@pytest.mark.asyncio
async def test_trigger_and_set(workflow_def, ctx):
    nodes = {n.name: n for n in workflow_def.nodes}

    # Step 1: manualTrigger
    trigger_result = await ManualTriggerExecutor().execute(
        nodes["When clicking 'Execute Workflow'"], [], ctx
    )
    assert trigger_result.status == NodeStatus.SUCCESS
    ctx.node_results["When clicking 'Execute Workflow'"] = trigger_result

    # Step 2: set node
    set_result = await SetNodeExecutor().execute(
        nodes["Set User Data"], trigger_result.output_data[0], ctx
    )
    assert set_result.status == NodeStatus.SUCCESS
    assert set_result.output_data[0][0]["userName"] == "Bong"


@pytest.mark.asyncio
async def test_http_node_query_params(workflow_def, ctx, respx_mock):
    """HttpRequest node builds query params from queryParametersUi and hits the URL."""
    import respx
    import httpx
    from flow_engine.nodes.http_request import HttpRequestExecutor

    nodes = {n.name: n for n in workflow_def.nodes}

    # Seed context with Set User Data result
    ctx.node_results["Set User Data"] = NodeResult(
        node_name="Set User Data",
        node_id="2",
        status=NodeStatus.SUCCESS,
        output_data=[[{"userName": "Bong"}]],
    )

    respx_mock.get("https://httpbin.org/get").mock(
        return_value=httpx.Response(200, json={"args": {"name": "Bong"}})
    )

    result = await HttpRequestExecutor().execute(
        nodes["Call External API"],
        [{"userName": "Bong"}],
        ctx,
    )
    assert result.status == NodeStatus.SUCCESS
    assert result.output_data[0][0]["args"]["name"] == "Bong"
