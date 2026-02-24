from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from flow_engine.models.execution import ExecutionContext, NodeResult
from flow_engine.models.node import NodeDefinition


class BaseNodeExecutor(ABC):
    """Abstract base class for all node executors."""

    @abstractmethod
    async def execute(
        self,
        node: NodeDefinition,
        input_items: list[dict[str, Any]],
        context: ExecutionContext,
    ) -> NodeResult:
        """Execute the node and return a NodeResult."""
        ...
