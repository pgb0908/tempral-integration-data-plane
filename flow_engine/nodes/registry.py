from __future__ import annotations

from flow_engine.models.node import NodeType
from flow_engine.nodes.base import BaseNodeExecutor
from flow_engine.nodes.code_node import CodeNodeExecutor
from flow_engine.nodes.http_request import HttpRequestExecutor
from flow_engine.nodes.if_node import IfNodeExecutor
from flow_engine.nodes.no_op import NoOpExecutor
from flow_engine.nodes.set_node import SetNodeExecutor
from flow_engine.nodes.trigger import ManualTriggerExecutor

_REGISTRY: dict[str, BaseNodeExecutor] = {
    NodeType.MANUAL_TRIGGER: ManualTriggerExecutor(),
    NodeType.SET: SetNodeExecutor(),
    NodeType.HTTP_REQUEST: HttpRequestExecutor(),
    NodeType.IF: IfNodeExecutor(),
    NodeType.NO_OP: NoOpExecutor(),
    NodeType.CODE: CodeNodeExecutor(),
}


def get_executor(node_type: str) -> BaseNodeExecutor:
    executor = _REGISTRY.get(node_type)
    if executor is None:
        raise ValueError(f"No executor registered for node type: {node_type!r}")
    return executor
