from collections import defaultdict
import logging
import mimetypes
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from fastui import AnyComponent, FastUI, prebuilt_html
from fastui.forms import SelectSearchResponse

from webapp.routers.components.main_component import get_common_content

router = APIRouter()
logger = logging.getLogger()


@router.get('/favicon.ico')
async def favicon():
    file_name = "favicon.ico"
    file_path = Path(f"src/webapp/static/{file_name}")
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})


@router.get("/api/", response_model=FastUI, response_model_exclude_none=True)
async def root_page() -> list[AnyComponent]:
    logger.info('root router called')
    return get_common_content(title='English Buddy Bot Admin Panel')


@router.get('/api/files/{lesson_id}/', response_model=SelectSearchResponse)
async def files_search_view(lesson_id: int) -> SelectSearchResponse:
    files = defaultdict(list)
    directory = Path(f"src/webapp/static/lessons_images/{lesson_id}")
    directory.mkdir(parents=True, exist_ok=True)
    for file in directory.iterdir():
        mime_type = mimetypes.guess_type(file)[0]
        if mime_type in ['image/png', 'image/jpeg', 'image/gif', 'image/heic', 'image/tiff', 'image/webp']:
            files['files'].append({'value': file.name, 'label': file.name})
    options = [{'label': k, 'options': v} for k, v in files.items()]
    return SelectSearchResponse(options=options)


@router.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    return HTMLResponse(prebuilt_html(title='English buddy FastUI'))
