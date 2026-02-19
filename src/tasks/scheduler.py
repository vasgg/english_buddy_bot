from taskiq.schedule_sources import LabelScheduleSource
from taskiq.scheduler import TaskiqScheduler

from tasks.broker import broker

scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])
