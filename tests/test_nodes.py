from __future__ import annotations

import pytest

from flow_engine.models.execution import ExecutionContext, NodeStatus
from flow_engine.models.node import NodeDefinition, NodeType
from flow_engine.nodes.if_node import IfNodeExecutor
from flow_engine.nodes.no_op import NoOpExecutor
from flow_engine.nodes.set_node import SetNodeExecutor
from flow_engine.nodes.trigger import ManualTriggerExecutor


def make_context(**kwargs) -> ExecutionContext:
    defaults = dict(workflow_id="test-wf", run_id="test-run", initial_data=[])
    defaults.update(kwargs)
    return ExecutionContext(**defaults)


def make_node(node_type: str, parameters: dict | None = None, name: str = "Node") -> NodeDefinition:
    return NodeDefinition(id="1", name=name, type=node_type, parameters=parameters or {})


# ── ManualTrigger ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_manual_trigger_uses_initial_data():
    node = make_node(NodeType.MANUAL_TRIGGER)
    ctx = make_context(initial_data=[{"msg": "hello"}])
    result = await ManualTriggerExecutor().execute(node, [], ctx)
    assert result.status == NodeStatus.SUCCESS
    assert result.output_data[0] == [{"msg": "hello"}]


@pytest.mark.asyncio
async def test_manual_trigger_prefers_input_items():
    node = make_node(NodeType.MANUAL_TRIGGER)
    ctx = make_context(initial_data=[{"msg": "initial"}])
    result = await ManualTriggerExecutor().execute(node, [{"msg": "input"}], ctx)
    assert result.output_data[0] == [{"msg": "input"}]


# ── NoOp ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_noop_passthrough():
    node = make_node(NodeType.NO_OP)
    ctx = make_context()
    items = [{"a": 1}, {"b": 2}]
    result = await NoOpExecutor().execute(node, items, ctx)
    assert result.output_data[0] == items


# ── Set ───────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_adds_static_field():
    node = make_node(
        NodeType.SET,
        parameters={"values": {"string": [{"name": "greeting", "value": "hi"}]}},
    )
    ctx = make_context()
    result = await SetNodeExecutor().execute(node, [{"name": "Alice"}], ctx)
    assert result.output_data[0][0]["greeting"] == "hi"
    assert result.output_data[0][0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_set_evaluates_expression():
    node = make_node(
        NodeType.SET,
        parameters={
            "values": {
                "string": [
                    {"name": "greeting", "value": '={{ "Hello " + $json.name }}'}
                ]
            }
        },
    )
    ctx = make_context()
    result = await SetNodeExecutor().execute(node, [{"name": "World"}], ctx)
    assert result.output_data[0][0]["greeting"] == "Hello World"


# ── IF ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_if_routes_true_false():
    node = make_node(
        NodeType.IF,
        parameters={
            "conditions": {
                "number": [{"value1": "={{ $json.score }}", "operation": "larger", "value2": 50}]
            }
        },
    )
    ctx = make_context()
    items = [{"score": 80}, {"score": 30}, {"score": 60}]
    result = await IfNodeExecutor().execute(node, items, ctx)
    assert len(result.output_data) == 2
    true_scores = [i["score"] for i in result.output_data[0]]
    false_scores = [i["score"] for i in result.output_data[1]]
    assert true_scores == [80, 60]
    assert false_scores == [30]


@pytest.mark.asyncio
async def test_if_string_condition():
    node = make_node(
        NodeType.IF,
        parameters={
            "conditions": {
                "string": [{"value1": "={{ $json.status }}", "operation": "equal", "value2": "active"}]
            }
        },
    )
    ctx = make_context()
    items = [{"status": "active"}, {"status": "inactive"}]
    result = await IfNodeExecutor().execute(node, items, ctx)
    assert result.output_data[0] == [{"status": "active"}]
    assert result.output_data[1] == [{"status": "inactive"}]
