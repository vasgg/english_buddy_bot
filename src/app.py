import logging.config

import sentry_sdk

from config import get_logging_config, get_settings
from webapp.create_app import create_app

logging_config = get_logging_config(__name__)
logging.config.dictConfig(logging_config)
logger = logging.getLogger()
settings = get_settings()

if settings.SENTRY_FASTAPI_DSN and settings.STAGE == 'prod':
    sentry_sdk.init(
        dsn=settings.SENTRY_FASTAPI_DSN.get_secret_value(),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )

app = create_app()
logger.info("webapp started")
