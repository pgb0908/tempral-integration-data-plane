from __future__ import annotations

import copy
from typing import Any

from flow_engine.expression.evaluator import ExpressionEvaluator
from flow_engine.models.execution import ExecutionContext, NodeResult, NodeStatus
from flow_engine.models.node import NodeDefinition
from flow_engine.nodes.base import BaseNodeExecutor


class SetNodeExecutor(BaseNodeExecutor):
    """
    Set node: adds or overwrites fields on each item.

    parameters.values supports:
      - string: [{"name": "...", "value": "..."}]
      - number: [{"name": "...", "value": 0}]
      - boolean: [{"name": "...", "value": true}]
    """

    async def execute(
        self,
        node: NodeDefinition,
        input_items: list[dict[str, Any]],
        context: ExecutionContext,
    ) -> NodeResult:
        values_config: dict[str, list[dict]] = node.parameters.get("values", {})
        output_items: list[dict[str, Any]] = []

        for item in input_items:
            new_item = copy.deepcopy(item)
            evaluator = ExpressionEvaluator(
                current_item=item,
                node_results={k: v.model_dump() for k, v in context.node_results.items()},
            )
            for _type_key in ("string", "number", "boolean"):
                for entry in values_config.get(_type_key, []):
                    name = entry.get("name", "")
                    raw_value = entry.get("value")
                    new_item[name] = evaluator.evaluate(raw_value)
            output_items.append(new_item)

        return NodeResult(
            node_name=node.name,
            node_id=node.id,
            status=NodeStatus.SUCCESS,
            output_data=[output_items],
        )
