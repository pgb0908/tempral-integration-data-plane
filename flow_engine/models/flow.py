from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FlowDeployment(BaseModel):
    flow_id: str
    name: str
    workflow_definition: dict[str, Any]
    version: int = 1
    created_at: datetime
    updated_at: datetime
