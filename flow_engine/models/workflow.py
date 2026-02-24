from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from flow_engine.models.node import NodeDefinition


# connections: { "NodeName": { "main": [ [ {"node": "...", "type": "main", "index": 0} ] ] } }
ConnectionTarget = dict[str, Any]
PortConnections = list[list[ConnectionTarget]]
NodeConnections = dict[str, PortConnections]  # {"main": [...]}
ConnectionsMap = dict[str, NodeConnections]


class WorkflowDefinition(BaseModel):
    name: str = "Unnamed Workflow"
    nodes: list[NodeDefinition] = Field(default_factory=list)
    connections: ConnectionsMap = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
