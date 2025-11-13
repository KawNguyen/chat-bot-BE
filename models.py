from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid

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
