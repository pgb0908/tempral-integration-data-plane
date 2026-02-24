from __future__ import annotations

from temporalio.client import Client

_temporal_client: Client | None = None


def set_temporal_client(client: Client) -> None:
    global _temporal_client
    _temporal_client = client


def get_temporal_client() -> Client:
    if _temporal_client is None:
        raise RuntimeError("Temporal client not initialized")
    return _temporal_client
