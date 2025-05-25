from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.weather_service import weather_service

app = FastAPI(
    title="SkyPeek",
    description="Приложение для получения прогноза погоды",
    version="1.0.0"
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/weather")
async def get_weather(city: str):
    """Получить прогноз погоды для города"""
    if not city.strip():
        raise HTTPException(status_code=400, detail="Название города не может быть пустым")
    
    weather_data = await weather_service.get_weather_by_city(city)
    
    if not weather_data:
        raise HTTPException(status_code=404, detail=f"Город '{city}' не найден")
    
    return weather_data

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "ok", "service": "skyPeek"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    