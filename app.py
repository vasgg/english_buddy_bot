import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from bot.database.db import db
from bot.database.models.slide import Slide
from bot.database.models.text import Text

app = FastAPI()
templates = Jinja2Templates(directory='src/API/templates')


@app.get('/', response_class=HTMLResponse)
async def read_root():
    html_content = Path('src/API/index.html').read_text()
    return HTMLResponse(content=html_content)


# @app.get("/texts", response_class=JSONResponse)
# async def get_texts():
#     try:
#         async with db.session_factory.begin() as db_session:
#             result = await db_session.execute(select(Text))
#             data = result.scalars().all()
#             return data
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.get("/slides", response_class=JSONResponse)
async def get_texts():
    try:
        async with db.session_factory.begin() as db_session:
            result = await db_session.execute(select(Slide))
            data = result.scalars().all()
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/texts", response_class=HTMLResponse)
async def read_texts(request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Text))
        data = result.scalars().all()
    return templates.TemplateResponse(request=request, name="texts.html", context={'texts': data})


@app.post("/save-texts")
async def save_texts(request: Request):
    try:
        async with db.session_factory.begin() as db_session:
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
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
