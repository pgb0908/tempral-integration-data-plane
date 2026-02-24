from __future__ import annotations

import copy
from typing import Any

import httpx

from flow_engine.expression.evaluator import ExpressionEvaluator
from flow_engine.models.execution import ExecutionContext, NodeResult, NodeStatus
from flow_engine.models.node import NodeDefinition
from flow_engine.nodes.base import BaseNodeExecutor


class HttpRequestExecutor(BaseNodeExecutor):
    """
    HTTP Request node: sends one HTTP request per input item.

    parameters:
      method: GET | POST | PUT | PATCH | DELETE (default GET)
      url: string (expression supported)
      headers: [{"name": ..., "value": ...}]
      queryParametersUi.parameter: [{"name": ..., "value": ...}]  (n8n UI style)
      queryParameters: [{"name": ..., "value": ...}]              (flat style)
      body: str | dict (for POST/PUT)
      responseFormat: json | text (default json)
    """

    async def execute(
        self,
        node: NodeDefinition,
        input_items: list[dict[str, Any]],
        context: ExecutionContext,
    ) -> NodeResult:
        params = node.parameters
        output_items: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for item in input_items:
                evaluator = ExpressionEvaluator(
                    current_item=item,
                    node_results={k: v.model_dump() for k, v in context.node_results.items()},
                )
                method = str(evaluator.evaluate(params.get("method", "GET"))).upper()
                url = str(evaluator.evaluate(params.get("url", "")))

                # Build headers
                headers: dict[str, str] = {}
                for h in params.get("headers", []):
                    headers[str(evaluator.evaluate(h["name"]))] = str(
                        evaluator.evaluate(h["value"])
                    )

                # Build query parameters
                # supports queryParametersUi.parameter (n8n UI) or queryParameters (flat)
                query_params: dict[str, str] = {}
                raw_qp = (
                    params.get("queryParametersUi", {}).get("parameter", [])
                    or params.get("queryParameters", [])
                )
                for qp in raw_qp:
                    key = str(evaluator.evaluate(qp["name"]))
                    val = str(evaluator.evaluate(qp["value"]))
                    query_params[key] = val

                # Build body
                body = params.get("body")
                if body is not None:
                    body = evaluator.evaluate(body)

                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=query_params if query_params else None,
                    json=body if isinstance(body, dict) else None,
                    content=body.encode() if isinstance(body, str) and body else None,
                )
                response.raise_for_status()

                response_format = params.get("responseFormat", "json")
                if response_format == "json":
                    try:
                        response_data = response.json()
                    except Exception:
                        response_data = {"text": response.text}
                else:
                    response_data = {"text": response.text}

                result_item = copy.deepcopy(item)
                if isinstance(response_data, dict):
                    result_item.update(response_data)
                else:
                    result_item["response"] = response_data
                output_items.append(result_item)

        return NodeResult(
            node_name=node.name,
            node_id=node.id,
            status=NodeStatus.SUCCESS,
            output_data=[output_items],
        )
