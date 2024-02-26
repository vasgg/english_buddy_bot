import logging.config

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sentry_sdk

from config import get_logging_config, settings
from webapp.routers.lessons_fastui import app as lessons_fastui_router
from webapp.routers.reactions_fastui import app as reaction_fastui_router
from webapp.routers.root_fastui import app as root_fastui_router
from webapp.routers.slides_fastui import app as slides_fastui_router
from webapp.routers.texts_fastui import app as texts_fastui_router

logging_config = get_logging_config(__name__)
logging.config.dictConfig(logging_config)
logger = logging.getLogger()


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
# app.include_router(lessons_fastui_router)
# app.include_router(lessons_fastui_router, prefix="/api")
app.include_router(slides_fastui_router, prefix="/api/slides")
app.include_router(texts_fastui_router, prefix="/api/texts")
app.include_router(reaction_fastui_router, prefix="/api/reactions")
app.include_router(lessons_fastui_router, prefix="/api/lessons")
app.include_router(root_fastui_router)
# app.include_router(root_router)
# app.include_router(texts_router)
# app.include_router(reactions_router)
# app.include_router(lessons_router)
# app.include_router(slides_router)
