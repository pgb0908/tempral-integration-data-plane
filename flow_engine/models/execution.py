from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


class NodeResult(BaseModel):
    node_name: str
    node_id: str
    status: NodeStatus
    # output_data[0] = port 0 items (true branch for IF), [1] = port 1 items (false branch)
    output_data: list[list[dict[str, Any]]] = Field(default_factory=lambda: [[]])
    error: str | None = None


class ExecutionContext(BaseModel):
    workflow_id: str
    run_id: str
    node_results: dict[str, NodeResult] = Field(default_factory=dict)
    current_node: str | None = None
    initial_data: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "running"
