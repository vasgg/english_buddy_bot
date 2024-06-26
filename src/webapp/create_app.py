from os.path import dirname, exists, join, realpath

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from webapp.routers.lessons import router as lessons_fastui_router
from webapp.routers.newsletter import router as newsletter_fastui_router
from webapp.routers.reactions import router as reaction_fastui_router
from webapp.routers.root import router as root_fastui_router
from webapp.routers.slides_get import router as slides_get_fastui_router
from webapp.routers.slides_post import router as slides_post_fastui_router
from webapp.routers.statistics import router as statistics_fastui_router
from webapp.routers.texts import router as texts_fastui_router
from webapp.routers.users import router as users_fastui_router

static_files_path = join(dirname(realpath(__file__)), 'static')
assert exists(static_files_path), static_files_path


def create_app():
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=static_files_path), name="static")
    app.include_router(slides_get_fastui_router, prefix="/api/slides")
    app.include_router(slides_post_fastui_router, prefix="/api/slides")
    app.include_router(users_fastui_router, prefix="/api/users")
    app.include_router(lessons_fastui_router, prefix="/api/lessons")
    app.include_router(texts_fastui_router, prefix="/api/texts")
    app.include_router(reaction_fastui_router, prefix="/api/reactions")
    app.include_router(newsletter_fastui_router, prefix="/api/newsletter")
    app.include_router(statistics_fastui_router, prefix="/api/statistics")
    app.include_router(root_fastui_router)
    return app
