from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from flow_engine.models.flow import FlowDeployment

STORE_DIR = Path("flows")


class FlowStore:
    def __init__(self, store_dir: Path = STORE_DIR) -> None:
        self._dir = store_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, flow_id: str) -> Path:
        return self._dir / f"{flow_id}.json"

    def save(self, deployment: FlowDeployment) -> None:
        self._path(deployment.flow_id).write_text(
            deployment.model_dump_json(), encoding="utf-8"
        )

    def get(self, flow_id: str) -> FlowDeployment | None:
        path = self._path(flow_id)
        if not path.exists():
            return None
        return FlowDeployment.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[FlowDeployment]:
        deployments = []
        for p in sorted(self._dir.glob("*.json")):
            try:
                deployments.append(
                    FlowDeployment.model_validate_json(p.read_text(encoding="utf-8"))
                )
            except Exception:
                pass
        return deployments

    def update(
        self,
        flow_id: str,
        new_def: dict,
        new_name: str | None = None,
    ) -> FlowDeployment:
        existing = self.get(flow_id)
        if existing is None:
            raise KeyError(flow_id)
        updated = existing.model_copy(
            update={
                "workflow_definition": new_def,
                "name": new_name if new_name is not None else existing.name,
                "version": existing.version + 1,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self.save(updated)
        return updated

    def delete(self, flow_id: str) -> bool:
        path = self._path(flow_id)
        if not path.exists():
            return False
        path.unlink()
        return True
