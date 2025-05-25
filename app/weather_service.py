import httpx
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class WeatherData(BaseModel):
    """Модель данных о погоде"""
    city: str
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    description: str
    timestamp: datetime

class WeatherService:
    """Сервис для работы с погодным API"""
    
    def __init__(self):
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.weather_base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.geocoding_base_url = "https://api.openweathermap.org/geo/1.0/direct"
    
    async def get_city_coordinates(self, city_name: str) -> Optional[Dict[str, Any]]:
        """Получить координаты города по названию через OpenWeatherMap"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "q": city_name,
                    "limit": 1,
                    "appid": self.api_key
                }
                response = await client.get(self.geocoding_base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if not data:
                    return None
                
                result = data[0]
                return {
                    "name": result["name"],
                    "latitude": result["lat"],
                    "longitude": result["lon"],
                    "country": result.get("country", ""),
                    "state": result.get("state", "")
                }
        except Exception as e:
            print(f"Ошибка при получении координат для {city_name}: {e}")
            return None
    
    async def get_weather_by_coordinates(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Получить данные о погоде по координатам через OpenWeatherMap"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self.api_key,
                    "units": "metric",  # Celsius
                    "lang": "ru"
                }
                response = await client.get(self.weather_base_url, params=params)
                response.raise_for_status()
                
                return response.json()
        except Exception as e:
            print(f"Ошибка при получении погоды: {e}")
            return None
    
    def _get_weather_description(self, weather_code: int) -> str:
        """Преобразовать код погоды в описание"""
        weather_codes = {
            0: "Ясно",
            1: "В основном ясно", 
            2: "Переменная облачность",
            3: "Пасмурно",
            45: "Туман",
            48: "Изморозь",
            51: "Легкая морось",
            53: "Умеренная морось", 
            55: "Сильная морось",
            61: "Легкий дождь",
            63: "Умеренный дождь",
            65: "Сильный дождь",
            71: "Легкий снег",
            73: "Умеренный снег",
            75: "Сильный снег",
            80: "Ливень",
            95: "Гроза"
        }
        return weather_codes.get(weather_code, "Неизвестно")
    
    async def get_weather_by_city(self, city_name: str) -> Optional[WeatherData]:
        """Получить погоду по названию города"""
        # Получаем координаты города
        coordinates = await self.get_city_coordinates(city_name)
        if not coordinates:
            return None
        
        # Получаем данные о погоде
        weather_data = await self.get_weather_by_coordinates(
            coordinates["latitude"], 
            coordinates["longitude"]
        )
        if not weather_data:
            return None
        
        # Форматируем данные
        main = weather_data["main"]
        weather = weather_data["weather"][0]
        wind = weather_data["wind"]
        
        # Формируем полное название города
        full_city_name = f"{coordinates['name']}"
        if coordinates.get("state"):
            full_city_name += f", {coordinates['state']}"
        if coordinates.get("country"):
            full_city_name += f", {coordinates['country']}"
        
        return WeatherData(
            city=full_city_name,
            temperature=main["temp"],
            feels_like=main["feels_like"],
            humidity=main["humidity"],
            wind_speed=wind.get("speed", 0),
            description=weather["description"].capitalize(),
            timestamp=datetime.now()
        )

# Создаем глобальный экземпляр сервиса
weather_service = WeatherService()
