from __future__ import annotations

from typing import Any

from flow_engine.models.workflow import WorkflowDefinition


class WorkflowParser:
    """Parses a raw JSON dict into a validated WorkflowDefinition."""

    @staticmethod
    def parse(data: dict[str, Any]) -> WorkflowDefinition:
        return WorkflowDefinition.model_validate(data)

    @staticmethod
    def parse_json(json_str: str) -> WorkflowDefinition:
        import json

        data = json.loads(json_str)
        return WorkflowParser.parse(data)
