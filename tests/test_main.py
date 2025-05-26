import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

class TestMainAPI:
    
    def test_health_check(self, client):
        """Тест health check эндпоинта"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "skyPeek"}
    
    def test_home_page(self, client):
        """Тест главной страницы"""
        response = client.get("/")
        assert response.status_code == 200
        assert "SkyPeek" in response.text
    
    def test_stats_page(self, client):
        """Тест страницы статистики"""
        response = client.get("/stats")
        assert response.status_code == 200
        assert "Статистика" in response.text
    
    def test_get_weather_missing_city(self, client):
        """Тест запроса погоды без города"""
        response = client.get("/api/weather")
        assert response.status_code == 422  # Validation error
    
    def test_get_weather_empty_city(self, client):
        """Тест запроса погоды с пустым городом"""
        response = client.get("/api/weather?city=")
        assert response.status_code == 400
        assert "не может быть пустым" in response.json()["detail"]
    
    @patch('app.main.weather_service.get_weather_by_city')
    def test_get_weather_city_not_found(self, mock_get_weather, client):
        """Тест запроса погоды для несуществующего города"""
        mock_get_weather.return_value = None
        
        response = client.get("/api/weather?city=NonexistentCity")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    @patch('app.main.weather_service.get_weather_by_city')
    def test_get_weather_success(self, mock_get_weather, client):
        """Тест успешного запроса погоды"""
        from app.weather_service import WeatherData
        from datetime import datetime
        
        mock_weather = WeatherData(
            city="Москва, Россия",
            temperature=15.5,
            feels_like=12.0,
            humidity=65,
            wind_speed=3.2,
            description="облачно",
            timestamp=datetime.now()
        )
        mock_get_weather.return_value = mock_weather
        
        response = client.get("/api/weather?city=Москва")
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Москва, Россия"
        assert data["temperature"] == 15.5
        assert data["humidity"] == 65
        assert data["description"] == "облачно"
    
    def test_get_search_history_empty(self, client):
        """Тест получения пустой истории поиска"""
        response = client.get("/api/history")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_search_history_with_data(self, client, sample_search_history, sample_user):
        """Тест получения истории поиска с данными"""
        response = client.get(
            "/api/history",
            cookies={"session_id": sample_user.session_id}  # Исправлено
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["city"] == "Санкт-Петербург, Россия"
        assert data[1]["city"] == "Москва, Россия"
    
    def test_get_last_city_with_data(self, client, sample_search_history, sample_user):
        """Тест получения последнего города с данными"""
        response = client.get(
            "/api/last-city",
            cookies={"session_id": sample_user.session_id}  # Используем правильный session_id
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["last_city"] == "Санкт-Петербург, Россия"
    
    def test_get_last_city_empty(self, client):
        """Тест получения последнего города для нового пользователя"""
        response = client.get("/api/last-city")
        assert response.status_code == 200
        assert response.json()["last_city"] is None
    
    def test_get_last_city_with_data(self, client, sample_search_history, sample_user):
            """Тест получения последнего города с данными"""
            response = client.get(
                "/api/last-city",
                cookies={"session_id": sample_user.session_id}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["last_city"] == "Санкт-Петербург, Россия"
    
    def test_get_stats_empty(self, client):
        """Тест получения статистики без данных"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["overview"]["total_searches"] == 0
        assert data["overview"]["total_users"] == 0
        assert data["overview"]["unique_cities"] == 0
        assert data["top_cities"] == []
    
    def test_get_stats_with_data(self, client, sample_search_history, sample_user):
        """Тест получения статистики с данными"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["overview"]["total_searches"] == 2
        assert data["overview"]["total_users"] == 1
        assert data["overview"]["unique_cities"] == 2
        assert len(data["top_cities"]) == 2
    
    def test_get_city_statistics_not_found(self, client):
        """Тест статистики по несуществующему городу"""
        response = client.get("/api/stats/city/NonexistentCity")
        assert response.status_code == 404
        assert "не найдена" in response.json()["detail"]
    
    def test_get_city_statistics_success(self, client, sample_search_history):
        """Тест статистики по существующему городу"""
        response = client.get("/api/stats/city/Москва")
        assert response.status_code == 200
        
        data = response.json()
        assert data["city"] == "Москва"
        assert data["statistics"]["total_searches"] == 1
        assert data["statistics"]["unique_users"] == 1
        assert data["weather_averages"]["temperature"] == 15.5
    
    def test_search_cities_short_query(self, client):
        """Тест поиска городов с коротким запросом"""
        response = client.get("/api/cities?q=M")
        assert response.status_code == 200
        assert response.json()["cities"] == []
    
    def test_search_cities_empty_query(self, client):
        """Тест поиска городов с пустым запросом"""
        response = client.get("/api/cities?q=")
        assert response.status_code == 200
        assert response.json()["cities"] == []
    
    @patch('httpx.AsyncClient')
    def test_search_cities_success(self, mock_client, client, sample_search_history, sample_user):
        """Тест успешного поиска городов"""
        from unittest.mock import MagicMock
        
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": "Moscow",
                "lat": 55.7558,
                "lon": 37.6176,
                "country": "RU"
            }
        ]
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        response = client.get("/api/cities?q=Мос")
        assert response.status_code == 200
        
        data = response.json()
        cities = data["cities"]
        assert len(cities) >= 1
        
        # Проверяем что есть результат из истории
        history_cities = [city for city in cities if city["source"] == "history"]
        assert len(history_cities) >= 1
        assert "Москва" in history_cities[0]["name"]