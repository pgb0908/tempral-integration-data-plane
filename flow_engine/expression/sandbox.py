from __future__ import annotations

from typing import Any


class AttrDict(dict):
    """dict subclass that allows attribute-style access: d.field == d['field']."""

    def __getattr__(self, name: str) -> Any:
        try:
            value = self[name]
        except KeyError:
            raise AttributeError(f"No attribute '{name}'") from None
        if isinstance(value, dict):
            return AttrDict(value)
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"No attribute '{name}'") from None


class NodeAccessor:
    """Proxy that supports $node['NodeName'].json access."""

    def __init__(self, node_results: dict) -> None:
        self._results = node_results

    def __getitem__(self, node_name: str) -> _NodeProxy:
        result = self._results.get(node_name)
        if result is None:
            raise KeyError(f"Node '{node_name}' has no result yet")
        return _NodeProxy(result)


class _NodeProxy:
    def __init__(self, node_result: Any) -> None:
        self._result = node_result

    @property
    def json(self) -> AttrDict:
        """Return the first item of the first output port."""
        output = self._result.get("output_data", [[]])
        port0 = output[0] if output else []
        item = port0[0] if port0 else {}
        return AttrDict(item)
