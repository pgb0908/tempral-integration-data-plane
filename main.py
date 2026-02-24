"""
Flow Engine entry point.

Usage:
    python main.py worker   – Start Temporal Worker
    python main.py api      – Start FastAPI server (port 8000)
    python main.py both     – Start Worker + API concurrently
"""

from __future__ import annotations

import asyncio
import sys

import uvicorn


async def run_worker() -> None:
    from flow_engine.temporal.worker import run_worker as _run_worker
    await _run_worker()


async def run_api() -> None:
    config = uvicorn.Config(
        "flow_engine.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_both() -> None:
    await asyncio.gather(run_worker(), run_api())


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"

    if mode == "worker":
        asyncio.run(run_worker())
    elif mode == "api":
        asyncio.run(run_api())
    elif mode == "both":
        asyncio.run(run_both())
    else:
        print(f"Unknown mode: {mode!r}. Use: worker | api | both")
        sys.exit(1)


if __name__ == "__main__":
    main()
