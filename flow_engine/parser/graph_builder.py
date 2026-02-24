from __future__ import annotations

from collections import deque
from typing import Any

from flow_engine.models.workflow import WorkflowDefinition


class WorkflowGraph:
    """
    Builds and queries a DAG from a WorkflowDefinition.

    edges[source] = { output_index: [target_node_name, ...] }
    reverse_edges[target] = [source_node_name, ...]
    """

    def __init__(self, workflow_def: WorkflowDefinition) -> None:
        self.nodes: dict[str, Any] = {n.name: n for n in workflow_def.nodes}
        # edges[src_name][output_index] = [dst_name, ...]
        self.edges: dict[str, dict[int, list[str]]] = {n.name: {} for n in workflow_def.nodes}
        # reverse_edges[dst_name] = [src_name, ...]
        self.reverse_edges: dict[str, list[str]] = {n.name: [] for n in workflow_def.nodes}

        self._build(workflow_def.connections)

    def _build(self, connections: dict) -> None:
        for source_name, port_map in connections.items():
            # port_map = {"main": [ [{"node": ..., "index": 0}], [...] ]}
            main_ports: list[list[dict]] = port_map.get("main", [])
            for output_index, targets in enumerate(main_ports):
                for target in targets:
                    target_name = target["node"]
                    self.edges[source_name].setdefault(output_index, []).append(target_name)
                    if target_name not in self.reverse_edges:
                        self.reverse_edges[target_name] = []
                    if source_name not in self.reverse_edges[target_name]:
                        self.reverse_edges[target_name].append(source_name)

    def get_start_nodes(self) -> list[str]:
        """Nodes with no incoming edges."""
        return [name for name, parents in self.reverse_edges.items() if not parents]

    def get_next_nodes(self, node_name: str, output_index: int = 0) -> list[str]:
        """Return downstream node names for a given output port."""
        return self.edges.get(node_name, {}).get(output_index, [])

    def topological_sort(self) -> list[str]:
        """
        Kahn's algorithm.  Returns nodes in execution order.
        Raises ValueError on cycles.
        """
        in_degree: dict[str, int] = {name: len(parents) for name, parents in self.reverse_edges.items()}
        queue: deque[str] = deque(n for n, d in in_degree.items() if d == 0)
        order: list[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for targets in self.edges.get(node, {}).values():
                for target in targets:
                    in_degree[target] -= 1
                    if in_degree[target] == 0:
                        queue.append(target)

        if len(order) != len(self.nodes):
            raise ValueError("Workflow graph contains a cycle")

        return order
