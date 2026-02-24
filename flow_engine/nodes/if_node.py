from __future__ import annotations

from typing import Any

from flow_engine.expression.evaluator import ExpressionEvaluator
from flow_engine.models.execution import ExecutionContext, NodeResult, NodeStatus
from flow_engine.models.node import NodeDefinition
from flow_engine.nodes.base import BaseNodeExecutor


class IfNodeExecutor(BaseNodeExecutor):
    """
    IF node: routes items to port 0 (true) or port 1 (false).

    parameters.conditions.string / .number / .boolean:
      [{"value1": ..., "operation": "equal|notEqual|contains|...", "value2": ...}]
    parameters.combineOperation: "all" | "any" (default "all")
    """

    _STRING_OPS = {
        "equal": lambda a, b: str(a) == str(b),
        "notEqual": lambda a, b: str(a) != str(b),
        "contains": lambda a, b: str(b) in str(a),
        "notContains": lambda a, b: str(b) not in str(a),
        "startsWith": lambda a, b: str(a).startswith(str(b)),
        "endsWith": lambda a, b: str(a).endswith(str(b)),
        "isEmpty": lambda a, _b: str(a) == "",
        "isNotEmpty": lambda a, _b: str(a) != "",
    }

    _NUMBER_OPS = {
        "equal": lambda a, b: float(a) == float(b),
        "notEqual": lambda a, b: float(a) != float(b),
        "larger": lambda a, b: float(a) > float(b),
        "largerEqual": lambda a, b: float(a) >= float(b),
        "smaller": lambda a, b: float(a) < float(b),
        "smallerEqual": lambda a, b: float(a) <= float(b),
    }

    _BOOL_OPS = {
        "equal": lambda a, b: bool(a) == bool(b),
        "notEqual": lambda a, b: bool(a) != bool(b),
        "isTrue": lambda a, _b: bool(a) is True,
        "isFalse": lambda a, _b: bool(a) is False,
    }

    async def execute(
        self,
        node: NodeDefinition,
        input_items: list[dict[str, Any]],
        context: ExecutionContext,
    ) -> NodeResult:
        conditions_config: dict = node.parameters.get("conditions", {})
        combine_op: str = node.parameters.get("combineOperation", "all")

        true_items: list[dict[str, Any]] = []
        false_items: list[dict[str, Any]] = []

        for item in input_items:
            evaluator = ExpressionEvaluator(
                current_item=item,
                node_results={k: v.model_dump() for k, v in context.node_results.items()},
            )
            if self._evaluate_conditions(conditions_config, evaluator, combine_op):
                true_items.append(item)
            else:
                false_items.append(item)

        return NodeResult(
            node_name=node.name,
            node_id=node.id,
            status=NodeStatus.SUCCESS,
            output_data=[true_items, false_items],
        )

    def _evaluate_conditions(
        self,
        conditions_config: dict,
        evaluator: ExpressionEvaluator,
        combine_op: str,
    ) -> bool:
        results: list[bool] = []

        for cond in conditions_config.get("string", []):
            v1 = evaluator.evaluate(cond.get("value1", ""))
            v2 = evaluator.evaluate(cond.get("value2", ""))
            op = cond.get("operation", "equal")
            fn = self._STRING_OPS.get(op)
            results.append(fn(v1, v2) if fn else False)

        for cond in conditions_config.get("number", []):
            v1 = evaluator.evaluate(cond.get("value1", 0))
            v2 = evaluator.evaluate(cond.get("value2", 0))
            op = cond.get("operation", "equal")
            fn = self._NUMBER_OPS.get(op)
            results.append(fn(v1, v2) if fn else False)

        for cond in conditions_config.get("boolean", []):
            v1 = evaluator.evaluate(cond.get("value1", False))
            v2 = evaluator.evaluate(cond.get("value2", False))
            op = cond.get("operation", "equal")
            fn = self._BOOL_OPS.get(op)
            results.append(fn(v1, v2) if fn else False)

        if not results:
            return True

        if combine_op == "any":
            return any(results)
        return all(results)
