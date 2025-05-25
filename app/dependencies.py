from fastapi import Cookie, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
import uuid

def get_or_create_user(session_id: str = Cookie(None), db: Session = Depends(get_db)) -> User:
    """Получить или создать пользователя по session_id из cookies"""
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    user = db.query(User).filter(User.session_id == session_id).first()
    
    if not user:
        user = User(session_id=session_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user
