from sqlalchemy.orm import Session
from sqlalchemy import desc
import models
from schemas import chat as schemas


def create_session(db: Session, user_id: str = None):
    """Tạo session chat mới"""
    db_session = models.ChatSession(user_id=user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session(db: Session, session_id: str):
    """Lấy session theo ID"""
    return db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()


def get_session_with_messages(db: Session, session_id: str, limit: int = 20):
    """Lấy session với lịch sử tin nhắn (giới hạn số lượng)"""
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not session:
        return None
    
    # Lấy tin nhắn gần nhất
    messages = db.query(models.ChatMessage)\
        .filter(models.ChatMessage.session_id == session_id)\
        .order_by(desc(models.ChatMessage.created_at))\
        .limit(limit)\
        .all()
    
    # Đảo ngược để có thứ tự từ cũ đến mới
    session.messages = list(reversed(messages))
    return session


def add_message(db: Session, session_id: str, role: str, content: str):
    """Thêm tin nhắn vào session"""
    db_message = models.ChatMessage(
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Cập nhật updated_at của session
    session = get_session(db, session_id)
    if session:
        from datetime import datetime
        session.updated_at = datetime.utcnow()
        db.commit()
    
    return db_message


def delete_session(db: Session, session_id: str):
    """Xóa session và tất cả messages"""
    session = get_session(db, session_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def get_recent_sessions(db: Session, limit: int = 10):
    """Lấy các session gần nhất"""
    return db.query(models.ChatSession)\
        .order_by(desc(models.ChatSession.updated_at))\
        .limit(limit)\
        .all()
