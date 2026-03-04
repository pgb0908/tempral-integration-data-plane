from __future__ import annotations

from temporalio.client import Client

from flow_engine.store.flow_store import FlowStore

_temporal_client: Client | None = None
_flow_store: FlowStore | None = None


def set_temporal_client(client: Client) -> None:
    global _temporal_client
    _temporal_client = client


def get_temporal_client() -> Client:
    if _temporal_client is None:
        raise RuntimeError("Temporal client not initialized")
    return _temporal_client


def set_flow_store(store: FlowStore) -> None:
    global _flow_store
    _flow_store = store


def get_flow_store() -> FlowStore:
    if _flow_store is None:
        raise RuntimeError("FlowStore not initialized")
    return _flow_store
