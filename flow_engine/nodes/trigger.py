from __future__ import annotations

from typing import Any

from flow_engine.models.execution import ExecutionContext, NodeResult, NodeStatus
from flow_engine.models.node import NodeDefinition
from flow_engine.nodes.base import BaseNodeExecutor


class ManualTriggerExecutor(BaseNodeExecutor):
    """Pass-through trigger: outputs initial_data or input_items unchanged."""

    async def execute(
        self,
        node: NodeDefinition,
        input_items: list[dict[str, Any]],
        context: ExecutionContext,
    ) -> NodeResult:
        items = input_items if input_items else context.initial_data
        return NodeResult(
            node_name=node.name,
            node_id=node.id,
            status=NodeStatus.SUCCESS,
            output_data=[items],
        )
