from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.weather_service import weather_service
from app.database import get_db
from app.dependencies import get_or_create_user
from app.models import User, SearchHistory
import asyncio
import httpx

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

@app.get("/api/stats")
async def get_search_statistics(db: Session = Depends(get_db)):
    """Получить статистику поисков по городам"""
    
    # Группируем по городам и считаем количество поисков
    city_stats = db.query(
        SearchHistory.city,
        func.count(SearchHistory.id).label('search_count'),
        func.max(SearchHistory.searched_at).label('last_searched')
    ).group_by(
        SearchHistory.city
    ).order_by(
        desc('search_count')
    ).limit(20).all()
    
    # Общая статистика
    total_searches = db.query(func.count(SearchHistory.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    
    # Статистика по дням (последние 7 дней)
    from datetime import datetime, timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    daily_stats = db.query(
        func.date(SearchHistory.searched_at).label('date'),
        func.count(SearchHistory.id).label('searches')
    ).filter(
        SearchHistory.searched_at >= seven_days_ago
    ).group_by(
        func.date(SearchHistory.searched_at)
    ).order_by('date').all()
    
    return {
        "overview": {
            "total_searches": total_searches,
            "total_users": total_users,
            "unique_cities": len(city_stats)
        },
        "top_cities": [
            {
                "city": stat.city,
                "search_count": stat.search_count,
                "last_searched": stat.last_searched
            }
            for stat in city_stats
        ],
        "daily_stats": [
            {
                "date": str(stat.date),
                "searches": stat.searches
            }
            for stat in daily_stats
        ]
    }

@app.get("/api/stats/city/{city_name}")
async def get_city_statistics(city_name: str, db: Session = Depends(get_db)):
    """Получить детальную статистику по конкретному городу"""
    
    # Основная статистика по городу
    city_searches = db.query(SearchHistory).filter(
        SearchHistory.city.ilike(f"%{city_name}%")
    ).all()
    
    if not city_searches:
        raise HTTPException(status_code=404, detail=f"Статистика для города '{city_name}' не найдена")
    
    # Подсчеты
    total_searches = len(city_searches)
    unique_users = len(set(search.user_id for search in city_searches))
    
    # Средние значения погоды
    avg_temp = sum(search.temperature for search in city_searches) / total_searches
    avg_humidity = sum(search.humidity for search in city_searches) / total_searches
    avg_wind = sum(search.wind_speed for search in city_searches) / total_searches
    
    # Самые частые описания погоды
    from collections import Counter
    weather_descriptions = Counter(search.description for search in city_searches)
    
    return {
        "city": city_name,
        "statistics": {
            "total_searches": total_searches,
            "unique_users": unique_users,
            "first_search": min(search.searched_at for search in city_searches),
            "last_search": max(search.searched_at for search in city_searches)
        },
        "weather_averages": {
            "temperature": round(avg_temp, 1),
            "humidity": round(avg_humidity, 1),
            "wind_speed": round(avg_wind, 1)
        },
        "popular_conditions": [
            {"condition": condition, "count": count}
            for condition, count in weather_descriptions.most_common(5)
        ]
    }

@app.get("/api/cities")
async def search_cities(q: str, db: Session = Depends(get_db)):
    """Поиск городов для автодополнения"""
    if not q or len(q.strip()) < 2:
        return {"cities": []}
    
    query = q.strip()
    
    try:
        # Сначала ищем в истории поиска пользователей
        history_cities = db.query(SearchHistory.city).filter(
            SearchHistory.city.ilike(f"%{query}%")
        ).distinct().limit(5).all()
        
        history_suggestions = [{"name": city[0], "source": "history"} for city in history_cities]
        
        # Если мало результатов из истории, ищем через Geocoding API
        suggestions = history_suggestions.copy()
        
        if len(suggestions) < 5:
            try:
                async with httpx.AsyncClient() as client:
                    params = {
                        "q": query,
                        "limit": 8,
                        "appid": weather_service.api_key
                    }
                    response = await client.get(weather_service.geocoding_base_url, params=params)
                    response.raise_for_status()
                    
                    api_cities = response.json()
                    
                    for city_data in api_cities:
                        city_name = city_data["name"]
                        if city_data.get("state"):
                            city_name += f", {city_data['state']}"
                        if city_data.get("country"):
                            city_name += f", {city_data['country']}"
                        
                        # Проверяем что такого города еще нет в suggestions
                        if not any(s["name"].lower() == city_name.lower() for s in suggestions):
                            suggestions.append({
                                "name": city_name,
                                "source": "api"
                            })
                        
                        if len(suggestions) >= 8:
                            break
                            
            except Exception as e:
                print(f"Ошибка поиска городов через API: {e}")
        
        return {"cities": suggestions[:8]}
        
    except Exception as e:
        print(f"Ошибка поиска городов: {e}")
        return {"cities": []}

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Страница статистики"""
    return templates.TemplateResponse("stats.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "ok", "service": "skyPeek"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
