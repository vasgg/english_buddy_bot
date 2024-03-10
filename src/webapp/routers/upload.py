from fastapi import APIRouter, UploadFile
from fastapi.responses import HTMLResponse

app = APIRouter()


@app.post("/image/{slide_id}/")
async def create_upload_file(slide_id: int, file: UploadFile):
    return {"filename": file.filename}


@app.get("/image/{slide_id}/", response_class=HTMLResponse)
async def main():
    content = """
<body>
<h1>Загрузка картинки</h1>
<form action="/image/{slide_id}/" enctype="multipart/form-data" method="post">
<input name="file" type="file">
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)
