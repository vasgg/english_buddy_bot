from __future__ import annotations

import argparse
import logging.config
import os
from pathlib import Path

from taskiq.cli.common_args import LogLevel
from taskiq.cli.worker.args import WorkerArgs
from taskiq.cli.worker.run import run_worker

from config import get_logging_config


def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(override=False)


def run_main(argv: list[str] | None = None) -> None:
    _maybe_load_dotenv()

    parser = argparse.ArgumentParser(description="Run Taskiq worker for this project.")
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=int(os.getenv("TASKIQ_WORKERS", "1")),
        help="Number of worker child processes.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("TASKIQ_LOG_LEVEL", "INFO").upper(),
        choices=["INFO", "WARNING", "DEBUG", "ERROR", "CRITICAL"],
        help="Worker log level.",
    )
    parser.add_argument(
        "--max-async-tasks",
        type=int,
        default=int(os.getenv("TASKIQ_MAX_ASYNC_TASKS", "100")),
        help="Maximum simultaneous async tasks per worker process.",
    )
    args = parser.parse_args(argv)

    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(get_logging_config("taskiq_worker"))

    worker_args = WorkerArgs(
        broker="tasks.broker:broker",
        modules=["tasks.tasks"],
        workers=max(1, args.workers),
        log_level=LogLevel[args.log_level],
        configure_logging=False,
        max_async_tasks=max(1, args.max_async_tasks),
    )
    exit_code = run_worker(worker_args)
    if exit_code:
        raise SystemExit(exit_code)
