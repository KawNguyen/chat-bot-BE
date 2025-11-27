from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

# Bảng hãng (Brand)
class Brand(Base):
    __tablename__ = "brands"

    id = Column(String, primary_key=True, index=True, default=lambda:str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)

    headphones = relationship("Headphone", back_populates="brand")


# Bảng loại tai nghe (Type)
class Type(Base):
    __tablename__ = "types"

    id = Column(String, primary_key=True, index=True, default=lambda:str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)

    headphones = relationship("Headphone", back_populates="type")


# Bảng tai nghe (Headphone)
class Headphone(Base):
    __tablename__ = "headphones"

    id = Column(String, primary_key=True, index=True, default=lambda:str(uuid.uuid4()))
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    price = Column(Integer)

    brand_id = Column(String, ForeignKey("brands.id"), nullable=True)
    type_id = Column(String, ForeignKey("types.id"), nullable=True)

    brand = relationship("Brand", back_populates="headphones")
    type = relationship("Type", back_populates="headphones")


# Bảng Chat Session - Lưu trữ phiên chat
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, index=True, default=lambda:str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=True)  # Optional user tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


# Bảng Chat Message - Lưu trữ từng tin nhắn
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, index=True, default=lambda:str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")
