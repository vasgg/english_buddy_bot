from collections import defaultdict
import logging
import mimetypes
from pathlib import Path
from random import randint

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from fastui import AnyComponent, FastUI, components as c, prebuilt_html
from fastui.forms import SelectSearchResponse

from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get('/favicon.ico')
async def favicon():
    file_name = "favicon.ico"
    file_path = Path(f"src/webapp/static/{file_name}")
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})


@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
async def root_page() -> list[AnyComponent]:
    logger.info('root router called')
    return get_common_content(c.Paragraph(text=f'test {randint(0, 1000)}'), title='Администрация')


@app.get('/api/files/{lesson_id}/', response_model=SelectSearchResponse)
async def files_search_view(lesson_id: int) -> SelectSearchResponse:
    files = defaultdict(list)
    directory = Path(f"src/webapp/static/images/lesson_{lesson_id}")
    for file in directory.iterdir():
        mime_type = mimetypes.guess_type(file)[0]
        if mime_type in ['image/png', 'image/jpeg', 'image/gif', 'image/heic', 'image/tiff', 'image/webp']:
            file_name = file.name.replace("-", "_").replace(" ", "_")
            files['files'].append({'value': file_name, 'label': file_name})
    options = [{'label': k, 'options': v} for k, v in files.items()]
    return SelectSearchResponse(options=options)


@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    return HTMLResponse(prebuilt_html(title='English buddy FastUI'))
