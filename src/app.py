import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from webapp.routers.lessons import lessons_router
from webapp.routers.reactions import reactions_router
from webapp.routers.root import root_router
from webapp.routers.slides import slides_router
from webapp.routers.texts import texts_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: " "%(filename)s: " "%(levelname)s: " "%(funcName)s(): " "%(lineno)d:\t" "%(message)s",
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/webapp/static"), name="static")
app.include_router(root_router)
app.include_router(texts_router)
app.include_router(reactions_router)
app.include_router(lessons_router)
app.include_router(slides_router)
