from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

root_router = APIRouter()
templates = Jinja2Templates(directory='src/app/templates')


@root_router.get('/', response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
