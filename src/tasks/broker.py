from taskiq_redis import RedisAsyncBroker

from config import get_settings


settings = get_settings()
broker = RedisAsyncBroker(settings.TASKIQ_REDIS_URL)
