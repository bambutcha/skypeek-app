from fastapi import Cookie, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

# Кэш для пользователей в рамках одного запроса
_user_cache = {}

def get_or_create_user(
    request: Request,
    session_id: str = Cookie(None), 
    db: Session = Depends(get_db)
) -> User:
    """Получить или создать пользователя по session_id из cookies с кэшированием"""
    
    # Проверяем кэш для текущего запроса
    cache_key = f"user_{session_id}_{id(request)}"
    if cache_key in _user_cache:
        return _user_cache[cache_key]
    
    if not session_id:
        session_id = str(uuid.uuid4())
        cache_key = f"user_{session_id}_{id(request)}"
    
    # Ищем пользователя в БД
    user = db.query(User).filter(User.session_id == session_id).first()
    
    if not user:
        user = User(session_id=session_id)
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except Exception:
            # Если произошла ошибка уникальности, перечитываем
            db.rollback()
            user = db.query(User).filter(User.session_id == session_id).first()
            if not user:
                session_id = str(uuid.uuid4())
                user = User(session_id=session_id)
                db.add(user)
                db.commit()
                db.refresh(user)
    
    # Кэшируем пользователя для текущего запроса
    _user_cache[cache_key] = user
    return user

class ClearUserCacheMiddleware(BaseHTTPMiddleware):
    """Middleware для очистки кеша пользователей после каждого запроса"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Очищаем кэш для завершенного запроса
        request_id = id(request)
        keys_to_remove = [key for key in _user_cache.keys() if key.endswith(f"_{request_id}")]
        for key in keys_to_remove:
            _user_cache.pop(key, None)
        
        return response
