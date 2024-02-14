import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from database.db import AsyncDBSession, db
from database.models.text import Text

texts_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')


@texts_router.get("/texts", response_class=HTMLResponse)
async def read_texts(request: Request, db_session: AsyncDBSession):
    result = await db_session.execute(select(Text))
    data = result.scalars().all()
    return templates.TemplateResponse(request=request, name="texts.html", context={'texts': data})


@texts_router.post("/texts")
async def save_texts(request: Request, db_session: AsyncDBSession):
    form_data = await request.form()
    for key, value in form_data.items():
        logging.info(f"Updating text for prompt: {key}")
        db_text = await db_session.execute(select(Text).where(Text.prompt == key))
        db_text = db_text.scalar_one_or_none()
        if db_text:
            db_text.text = value
        else:
            raise HTTPException(status_code=404, detail=f"Text with prompt '{key}' not found")
    await db_session.commit()
    return {"message": "Texts updated successfully"}
