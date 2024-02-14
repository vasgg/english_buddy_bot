import logging.config

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sentry_sdk

from config import get_logging_config, settings
from webapp.routers.lessons import lessons_router
from webapp.routers.reactions import reactions_router
from webapp.routers.root import root_router
from webapp.routers.slides import slides_router
from webapp.routers.texts import texts_router

logging_config = get_logging_config(__name__)
logging.config.dictConfig(logging_config)
logger = logging.getLogger('webapp')


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
app = FastAPI()
logger.info("webapp started")
app.mount("/static", StaticFiles(directory="src/webapp/static"), name="static")
app.include_router(root_router)
app.include_router(texts_router)
app.include_router(reactions_router)
app.include_router(lessons_router)
app.include_router(slides_router)
