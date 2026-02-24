from __future__ import annotations

from typing import Any

from temporalio import activity

from flow_engine.models.execution import ExecutionContext, NodeResult, NodeStatus
from flow_engine.models.node import NodeDefinition
from flow_engine.nodes.registry import get_executor


@activity.defn(name="execute_node_activity")
async def execute_node_activity(
    node_dict: dict[str, Any],
    input_items: list[dict[str, Any]],
    context_dict: dict[str, Any],
) -> dict[str, Any]:
    """
    Temporal Activity: deserializes arguments, runs the node executor,
    and returns the serialized NodeResult.
    """
    node = NodeDefinition.model_validate(node_dict)
    context = ExecutionContext.model_validate(context_dict)

    try:
        executor = get_executor(node.type)
        result: NodeResult = await executor.execute(node, input_items, context)
    except Exception as exc:
        result = NodeResult(
            node_name=node.name,
            node_id=node.id,
            status=NodeStatus.ERROR,
            output_data=[[]],
            error=str(exc),
        )

    return result.model_dump(mode="json")
