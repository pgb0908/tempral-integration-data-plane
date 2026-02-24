from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from flow_engine.models.execution import ExecutionContext, NodeResult, NodeStatus
    from flow_engine.models.workflow import WorkflowDefinition
    from flow_engine.parser.graph_builder import WorkflowGraph
    from flow_engine.parser.workflow_parser import WorkflowParser
    from flow_engine.temporal.activities import execute_node_activity


@workflow.defn(name="FlowWorkflow")
class FlowWorkflow:
    def __init__(self) -> None:
        self._status: str = "running"
        self._current_node: str | None = None
        self._completed_nodes: list[str] = []
        self._cancelled: bool = False

    @workflow.run
    async def run(self, request: dict[str, Any]) -> dict[str, Any]:
        workflow_def: WorkflowDefinition = WorkflowParser.parse(
            request["workflow_definition"]
        )
        graph = WorkflowGraph(workflow_def)

        context = ExecutionContext(
            workflow_id=workflow.info().workflow_id,
            run_id=workflow.info().run_id,
            initial_data=request.get("initial_data", []),
        )

        try:
            execution_order = graph.topological_sort()
        except ValueError as exc:
            self._status = "error"
            return {"status": "error", "error": str(exc)}

        # node_inputs accumulates the items that should flow into each node
        node_inputs: dict[str, list[dict[str, Any]]] = {}

        # Inject initial_data into start nodes
        for start_node in graph.get_start_nodes():
            node_inputs[start_node] = context.initial_data

        retry_policy = RetryPolicy(
            maximum_attempts=3,
            non_retryable_error_types=["ValueError"],
        )

        for node_name in execution_order:
            if self._cancelled:
                self._status = "cancelled"
                break

            node_def = graph.nodes.get(node_name)
            if node_def is None:
                continue

            self._current_node = node_name
            context.current_node = node_name
            input_items = node_inputs.get(node_name, [])

            result_dict: dict[str, Any] = await workflow.execute_activity(
                execute_node_activity,
                args=[
                    node_def.model_dump(mode="json"),
                    input_items,
                    context.model_dump(mode="json"),
                ],
                start_to_close_timeout=timedelta(seconds=300),
                retry_policy=retry_policy,
            )

            result = NodeResult.model_validate(result_dict)
            context.node_results[node_name] = result
            self._completed_nodes.append(node_name)

            if result.status == NodeStatus.ERROR:
                self._status = "error"
                context.status = "error"
                return context.model_dump(mode="json")

            # Route outputs to downstream nodes
            for output_index, port_items in enumerate(result.output_data):
                for next_node in graph.get_next_nodes(node_name, output_index):
                    existing = node_inputs.get(next_node, [])
                    node_inputs[next_node] = existing + port_items

        if not self._cancelled:
            self._status = "completed"
            context.status = "completed"

        return context.model_dump(mode="json")

    @workflow.query(name="get_status")
    def get_status(self) -> dict[str, Any]:
        return {
            "status": self._status,
            "current_node": self._current_node,
            "completed_nodes": self._completed_nodes,
        }

    @workflow.signal(name="cancel_workflow")
    async def cancel_workflow(self) -> None:
        self._cancelled = True
