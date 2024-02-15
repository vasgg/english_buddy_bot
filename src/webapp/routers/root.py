from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

root_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')


@root_router.get('/', response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@root_router.get('/favicon.ico')
async def favicon():
    file_name = "favicon.ico"
    file_path = Path(f"src/webapp/static/{file_name}")
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})
