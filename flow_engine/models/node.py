from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    MANUAL_TRIGGER = "n8n-nodes-base.manualTrigger"
    SET = "n8n-nodes-base.set"
    HTTP_REQUEST = "n8n-nodes-base.httpRequest"
    IF = "n8n-nodes-base.if"
    NO_OP = "n8n-nodes-base.noOp"
    CODE = "n8n-nodes-base.code"


class NodeDefinition(BaseModel):
    id: str
    name: str
    type: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    position: list[float] | None = None
