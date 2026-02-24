from __future__ import annotations

import json
import pathlib

import pytest

from flow_engine.models.node import NodeType
from flow_engine.parser.graph_builder import WorkflowGraph
from flow_engine.parser.workflow_parser import WorkflowParser

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "sample_workflow.json"


@pytest.fixture
def sample_def():
    return WorkflowParser.parse(json.loads(FIXTURE.read_text()))


def test_parse_nodes(sample_def):
    assert len(sample_def.nodes) == 4
    assert sample_def.nodes[0].type == NodeType.MANUAL_TRIGGER


def test_parse_connections(sample_def):
    assert "Start" in sample_def.connections
    assert "SetGreeting" in sample_def.connections


def test_graph_start_nodes(sample_def):
    graph = WorkflowGraph(sample_def)
    starts = graph.get_start_nodes()
    assert starts == ["Start"]


def test_topological_sort(sample_def):
    graph = WorkflowGraph(sample_def)
    order = graph.topological_sort()
    assert order.index("Start") < order.index("SetGreeting")
    assert order.index("SetGreeting") < order.index("CheckName")
    assert order.index("CheckName") < order.index("PassThrough")


def test_get_next_nodes(sample_def):
    graph = WorkflowGraph(sample_def)
    assert graph.get_next_nodes("Start", 0) == ["SetGreeting"]
    assert graph.get_next_nodes("CheckName", 0) == ["PassThrough"]
    assert graph.get_next_nodes("CheckName", 1) == []


def test_cycle_detection():
    from flow_engine.models.node import NodeDefinition
    from flow_engine.models.workflow import WorkflowDefinition

    wf = WorkflowDefinition(
        name="Cyclic",
        nodes=[
            NodeDefinition(id="1", name="A", type="n8n-nodes-base.noOp"),
            NodeDefinition(id="2", name="B", type="n8n-nodes-base.noOp"),
        ],
        connections={
            "A": {"main": [[{"node": "B", "type": "main", "index": 0}]]},
            "B": {"main": [[{"node": "A", "type": "main", "index": 0}]]},
        },
    )
    graph = WorkflowGraph(wf)
    with pytest.raises(ValueError, match="cycle"):
        graph.topological_sort()
