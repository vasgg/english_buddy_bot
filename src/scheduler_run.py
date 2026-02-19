from __future__ import annotations

import argparse
import asyncio
import logging.config
import os
from pathlib import Path

from taskiq.cli.common_args import LogLevel
from taskiq.cli.scheduler.args import SchedulerArgs
from taskiq.cli.scheduler.run import run_scheduler

from config import get_logging_config


def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(override=False)


def run_main(argv: list[str] | None = None) -> None:
    _maybe_load_dotenv()

    parser = argparse.ArgumentParser(description="Run Taskiq scheduler for this project.")
    parser.add_argument(
        "--skip-first-run",
        action=argparse.BooleanOptionalAction,
        default=os.getenv("TASKIQ_SKIP_FIRST_RUN", "1").strip() not in {"0", "false", "no"},
        help="Skip first run of scheduler (recommended in prod).",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("TASKIQ_LOG_LEVEL", "INFO").upper(),
        choices=["INFO", "WARNING", "DEBUG", "ERROR", "CRITICAL"],
        help="Scheduler log level.",
    )
    parser.add_argument(
        "--update-interval",
        type=int,
        default=None,
        help="Interval in seconds to check for new schedules. Default is Taskiq's default.",
    )
    parser.add_argument(
        "--loop-interval",
        type=int,
        default=None,
        help="Interval in seconds to check tasks to send. Default is Taskiq's default.",
    )
    args = parser.parse_args(argv)

    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(get_logging_config("taskiq_scheduler"))

    scheduler_args = SchedulerArgs(
        scheduler="tasks.scheduler:scheduler",
        modules=["tasks.tasks"],
        skip_first_run=bool(args.skip_first_run),
        log_level=LogLevel[args.log_level],
        configure_logging=False,
        update_interval=args.update_interval,
        loop_interval=args.loop_interval,
    )
    asyncio.run(run_scheduler(scheduler_args))
