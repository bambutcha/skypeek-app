from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.weather_service import weather_service
from app.database import get_db
from app.dependencies import get_or_create_user
from app.models import User, SearchHistory

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
async def get_weather(
    city: str, 
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_or_create_user)
):
    """Получить прогноз погоды для города и сохранить в историю"""
    if not city.strip():
        raise HTTPException(status_code=400, detail="Название города не может быть пустым")
    
    # Получаем данные о погоде
    weather_data = await weather_service.get_weather_by_city(city)
    
    if not weather_data:
        raise HTTPException(status_code=404, detail=f"Город '{city}' не найден")
    
    # Сохраняем в историю поиска
    search_record = SearchHistory(
        user_id=user.id,
        city=weather_data.city,
        temperature=weather_data.temperature,
        feels_like=weather_data.feels_like,
        humidity=weather_data.humidity,
        wind_speed=weather_data.wind_speed,
        description=weather_data.description
    )
    
    db.add(search_record)
    db.commit()
    db.refresh(search_record)
    
    # Устанавливаем cookie с session_id (если еще не установлен)
    if not request.cookies.get("session_id"):
        response.set_cookie(
            key="session_id",
            value=user.session_id,
            max_age=30*24*60*60,  # 30 дней
            httponly=True,
            samesite="lax"
        )
    
    return weather_data

@app.get("/api/history")
async def get_search_history(
    user: User = Depends(get_or_create_user),
    db: Session = Depends(get_db)
):
    """Получить историю поиска пользователя"""
    searches = db.query(SearchHistory).filter(
        SearchHistory.user_id == user.id
    ).order_by(SearchHistory.searched_at.desc()).limit(10).all()
    
    return [
        {
            "id": search.id,
            "city": search.city,
            "temperature": search.temperature,
            "feels_like": search.feels_like,
            "humidity": search.humidity,
            "wind_speed": search.wind_speed,
            "description": search.description,
            "searched_at": search.searched_at
        }
        for search in searches
    ]

@app.get("/api/last-city")
async def get_last_searched_city(
    user: User = Depends(get_or_create_user),
    db: Session = Depends(get_db)
):
    """Получить последний искомый город пользователя"""
    last_search = db.query(SearchHistory).filter(
        SearchHistory.user_id == user.id
    ).order_by(SearchHistory.searched_at.desc()).first()
    
    if not last_search:
        return {"last_city": None}
    
    return {
        "last_city": last_search.city,
        "searched_at": last_search.searched_at
    }

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "ok", "service": "skyPeek"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    