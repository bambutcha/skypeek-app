import pytest
from app.models import User, SearchHistory

class TestModels:
    
    def test_user_creation(self, db_session):
        """Тест создания пользователя"""
        user = User(session_id="test-session-456")
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.session_id == "test-session-456"
        assert user.created_at is not None
    
    def test_search_history_creation(self, db_session, sample_user):
        """Тест создания записи истории поиска"""
        search = SearchHistory(
            user_id=sample_user.id,
            city="Новосибирск, Россия",
            temperature=5.0,
            feels_like=2.0,
            humidity=80,
            wind_speed=2.1,
            description="снег"
        )
        db_session.add(search)
        db_session.commit()
        
        assert search.id is not None
        assert search.user_id == sample_user.id
        assert search.city == "Новосибирск, Россия"
        assert search.searched_at is not None
    
    def test_user_searches_relationship(self, db_session, sample_user, sample_search_history):
        """Тест связи между пользователем и историей поиска"""
        # Обновляем пользователя из БД чтобы получить связанные объекты
        db_session.refresh(sample_user)
        
        assert len(sample_user.searches) == 2
        assert sample_user.searches[0].city in ["Москва, Россия", "Санкт-Петербург, Россия"]
    
    def test_search_user_relationship(self, db_session, sample_search_history, sample_user):
        """Тест обратной связи от истории к пользователю"""
        search = sample_search_history[0]
        db_session.refresh(search)
        
        assert search.user is not None
        assert search.user.session_id == sample_user.session_id