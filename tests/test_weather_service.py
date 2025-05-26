import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.weather_service import WeatherService, WeatherData

class TestWeatherService:
    
    @pytest.fixture
    def weather_service(self):
        return WeatherService()
    
    @pytest.mark.asyncio
    async def test_get_city_coordinates_success(self, weather_service):
        """Тест успешного получения координат города"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": "Moscow",
                "lat": 55.7558,
                "lon": 37.6176,
                "country": "RU",
                "state": "Moscow"
            }
        ]
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await weather_service.get_city_coordinates("Moscow")
            
            assert result is not None
            assert result["name"] == "Moscow" 
            assert result["latitude"] == 55.7558
            assert result["longitude"] == 37.6176
            assert result["country"] == "RU"
    
    @pytest.mark.asyncio
    async def test_get_city_coordinates_not_found(self, weather_service):
        """Тест когда город не найден"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await weather_service.get_city_coordinates("NonexistentCity")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_weather_by_coordinates_success(self, weather_service):
        """Тест успешного получения погоды по координатам"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "main": {
                "temp": 15.5,
                "feels_like": 12.0,
                "humidity": 65
            },
            "weather": [
                {
                    "description": "облачно"
                }
            ],
            "wind": {
                "speed": 3.2
            }
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await weather_service.get_weather_by_coordinates(55.7558, 37.6176)
            
            assert result is not None
            assert result["main"]["temp"] == 15.5
            assert result["main"]["humidity"] == 65
            assert result["weather"][0]["description"] == "облачно"
    
    @pytest.mark.asyncio
    async def test_get_weather_by_city_success(self, weather_service):
        """Тест полного процесса получения погоды по городу"""
        # Мокаем координаты
        coordinates_response = MagicMock()
        coordinates_response.json.return_value = [
            {
                "name": "Moscow",
                "lat": 55.7558,
                "lon": 37.6176,
                "country": "RU"
            }
        ]
        coordinates_response.raise_for_status = MagicMock()
        
        # Мокаем погоду
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "main": {
                "temp": 15.5,
                "feels_like": 12.0,
                "humidity": 65
            },
            "weather": [
                {
                    "description": "облачно"
                }
            ],
            "wind": {
                "speed": 3.2
            }
        }
        weather_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get.side_effect = [
            coordinates_response, weather_response
        ]
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await weather_service.get_weather_by_city("Moscow")
            
            assert result is not None
            assert isinstance(result, WeatherData)
            assert result.city == "Moscow, RU"
            assert result.temperature == 15.5
            assert result.humidity == 65
            assert result.description == "Облачно"
            