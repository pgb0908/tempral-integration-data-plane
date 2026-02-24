from __future__ import annotations

import re
from typing import Any

from simpleeval import EvalWithCompoundTypes, InvalidExpression

from flow_engine.expression.sandbox import AttrDict, NodeAccessor

_EXPR_PATTERN = re.compile(r"=\{\{(.+?)\}\}", re.DOTALL)


class ExpressionEvaluator:
    """
    Evaluates n8n-style expressions like ={{ $json.field }} or ={{ $node['X'].json.val }}.

    Rules:
    - String starting with ={{ ... }} is treated as an expression.
    - Multiple expressions in one string are evaluated and concatenated.
    - Plain strings are returned as-is.
    """

    def __init__(
        self,
        current_item: dict[str, Any] | None = None,
        node_results: dict[str, Any] | None = None,
    ) -> None:
        self._current_item = current_item or {}
        self._node_results = node_results or {}

    # Mapping from expression alias → actual name used in simpleeval
    _ALIAS_MAP = {"$json": "_json_", "$node": "_node_"}

    def _build_names(self) -> dict[str, Any]:
        return {
            "_json_": AttrDict(self._current_item),
            "_node_": NodeAccessor(self._node_results),
        }

    @staticmethod
    def _preprocess(expr: str) -> str:
        """Replace $json and $node with Python-valid identifiers."""
        expr = expr.replace("$json", "_json_")
        expr = expr.replace("$node", "_node_")
        return expr

    def evaluate(self, value: Any) -> Any:
        """Evaluate a single value. Non-strings are returned unchanged."""
        if not isinstance(value, str):
            return value

        matches = list(_EXPR_PATTERN.finditer(value))
        if not matches:
            return value

        # Single full-string expression → return evaluated type directly
        if len(matches) == 1 and matches[0].start() == 0 and matches[0].end() == len(value):
            expr = matches[0].group(1).strip()
            return self._eval_expr(expr)

        # Multiple or partial expressions → stringify and concatenate
        result = value
        for match in reversed(matches):
            expr = match.group(1).strip()
            evaluated = str(self._eval_expr(expr))
            result = result[: match.start()] + evaluated + result[match.end() :]
        return result

    def evaluate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Recursively evaluate all expressions in a parameters dict."""
        return {k: self._eval_recursive(v) for k, v in parameters.items()}

    def _eval_recursive(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._eval_recursive(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._eval_recursive(item) for item in value]
        return self.evaluate(value)

    def _eval_expr(self, expr: str) -> Any:
        processed = self._preprocess(expr)
        evaluator = EvalWithCompoundTypes(names=self._build_names())
        try:
            return evaluator.eval(processed)
        except (InvalidExpression, Exception) as exc:
            raise ValueError(f"Expression evaluation failed: {expr!r} — {exc}") from exc
