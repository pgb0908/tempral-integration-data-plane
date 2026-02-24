from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from flow_engine.temporal.activities import execute_node_activity
from flow_engine.temporal.workflow import FlowWorkflow

TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "flow-engine"


async def run_worker(host: str = TEMPORAL_HOST, task_queue: str = TASK_QUEUE) -> None:
    client = await Client.connect(host)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[FlowWorkflow],
        activities=[execute_node_activity],
    )
    print(f"Worker started. Task queue: {task_queue!r}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
