from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from webapp.routers.lessons import router as lessons_fastui_router
from webapp.routers.newsletter import router as newsletter_fastui_router
from webapp.routers.reactions import router as reaction_fastui_router
from webapp.routers.root import router as root_fastui_router
from webapp.routers.slides import router as slides_fastui_router
from webapp.routers.texts import router as texts_fastui_router


def create_app():
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="src/webapp/static"), name="static")
    app.include_router(slides_fastui_router, prefix="/api/slides")
    app.include_router(lessons_fastui_router, prefix="/api/lessons")
    app.include_router(texts_fastui_router, prefix="/api/texts")
    app.include_router(reaction_fastui_router, prefix="/api/reactions")
    app.include_router(newsletter_fastui_router, prefix="/api/newsletter")
    app.include_router(root_fastui_router)
    return app
