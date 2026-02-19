import logging.config
from pathlib import Path

from taskiq.schedule_sources import LabelScheduleSource
from taskiq.scheduler import TaskiqScheduler

from config import get_logging_config
from tasks.broker import broker


logs_directory = Path("logs")
logs_directory.mkdir(parents=True, exist_ok=True)
logging.config.dictConfig(get_logging_config("taskiq_scheduler"))

scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])
