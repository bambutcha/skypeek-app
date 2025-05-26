import pytest
import os
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import User, SearchHistory

# Тестовая база данных в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_db():
    """Создание тестовой БД для каждого теста"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """Клиент для тестирования FastAPI"""
    return TestClient(app)

@pytest.fixture
def db_session(test_db):
    """Сессия БД для тестов"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def sample_user(db_session):
    """Создание тестового пользователя с уникальным session_id"""
    unique_session_id = f"test-session-{uuid.uuid4().hex[:8]}"
    user = User(session_id=unique_session_id)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_search_history(db_session, sample_user):
    """Создание тестовой истории поиска"""
    from datetime import datetime, timedelta
    
    # Создаем записи с разным временем
    searches = [
        SearchHistory(
            user_id=sample_user.id,
            city="Москва, Россия",
            temperature=15.5,
            feels_like=12.0,
            humidity=65,
            wind_speed=3.2,
            description="облачно",
            searched_at=datetime.now() - timedelta(minutes=10)  # Раньше
        ),
        SearchHistory(
            user_id=sample_user.id,
            city="Санкт-Петербург, Россия", 
            temperature=8.0,
            feels_like=5.0,
            humidity=78,
            wind_speed=4.5,
            description="дождь",
            searched_at=datetime.now()  # Позже (последний)
        )
    ]
    
    for search in searches:
        db_session.add(search)
    
    db_session.commit()
    return searches
