from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="SkyPeek",
    description="Приложение для получения прогноза погоды",
    version="1.0.0"
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности"""
    return {"status": "ok", "service": "skypeek-app"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    