from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.app.routers.lessons import lessons_router
from src.app.routers.reactions import reactions_router
from src.app.routers.root import root_router
from src.app.routers.slides import slides_router
from src.app.routers.texts import texts_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")
app.include_router(root_router)
app.include_router(texts_router)
app.include_router(reactions_router)
app.include_router(lessons_router)
app.include_router(slides_router)
