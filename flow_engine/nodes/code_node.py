from __future__ import annotations

import copy
from typing import Any

from flow_engine.models.execution import ExecutionContext, NodeResult, NodeStatus
from flow_engine.models.node import NodeDefinition
from flow_engine.nodes.base import BaseNodeExecutor


class CodeNodeExecutor(BaseNodeExecutor):
    """
    Code node: executes user-supplied Python code in a restricted sandbox.

    parameters:
      jsCode: str  (Python code; variable name follows n8n convention but contains Python)

    The code receives:
      - `items`: list of dicts (input items)
      - `return_data`: list to append output items to

    The code MUST populate `return_data`.  Example:
      for item in items:
          item['doubled'] = item['value'] * 2
          return_data.append(item)
    """

    _FORBIDDEN_BUILTINS = {
        "__import__", "open", "eval", "exec", "compile",
        "breakpoint", "input", "memoryview",
    }

    async def execute(
        self,
        node: NodeDefinition,
        input_items: list[dict[str, Any]],
        context: ExecutionContext,
    ) -> NodeResult:
        code: str = node.parameters.get("jsCode", "")
        if not code.strip():
            return NodeResult(
                node_name=node.name,
                node_id=node.id,
                status=NodeStatus.SUCCESS,
                output_data=[input_items],
            )

        safe_builtins = {
            k: v for k, v in __builtins__.items()  # type: ignore[union-attr]
            if k not in self._FORBIDDEN_BUILTINS
        } if isinstance(__builtins__, dict) else {
            k: getattr(__builtins__, k)
            for k in dir(__builtins__)
            if k not in self._FORBIDDEN_BUILTINS and not k.startswith("__")
        }

        items = copy.deepcopy(input_items)
        return_data: list[dict[str, Any]] = []
        local_vars: dict[str, Any] = {
            "items": items,
            "return_data": return_data,
        }

        exec(code, {"__builtins__": safe_builtins}, local_vars)  # noqa: S102

        result_items = local_vars.get("return_data", return_data)
        return NodeResult(
            node_name=node.name,
            node_id=node.id,
            status=NodeStatus.SUCCESS,
            output_data=[result_items],
        )
