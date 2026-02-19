from taskiq_redis import RedisStreamBroker

from config import get_settings


settings = get_settings()

# `queue_name` must be unique across projects if you share a single Redis instance.
queue_name = f"english_buddy_bot:{settings.STAGE.value}"

broker = RedisStreamBroker(
    settings.TASKIQ_REDIS_URL,
    queue_name=queue_name,
    consumer_group_name=queue_name,
)
