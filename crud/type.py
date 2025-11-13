from sqlalchemy.orm import Session
import models
from schemas import type as schemas
import re

def get_types(db: Session):
    return db.query(models.Type).all()

def get_type_by_slug(db: Session, slug: str):
    return db.query(models.Type).filter(models.Type.slug == slug).first()

def get_type_by_id(db: Session, type_id: str):
    return db.query(models.Type).filter(models.Type.id == type_id).first()

def create_slug_from_name(name: str) -> str:
    # Chuyển tên thành chữ thường
    slug = name.lower()
    # Thay thế khoảng trắng và các ký tự đặc biệt bằng dấu gạch ngang
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Loại bỏ các dấu gạch ngang thừa
    slug = re.sub(r'-{2,}', '-', slug).strip('-')
    return slug

def generate_unique_slug(db: Session, base_slug: str) -> str:
    """Tạo slug unique bằng cách thêm số suffix nếu cần"""
    original_slug = base_slug
    counter = 1
    
    while get_type_by_slug(db, base_slug):
        base_slug = f"{original_slug}-{counter}"
        counter += 1
    
    return base_slug

def create_type(db: Session, type: schemas.TypeCreate):
    # Kiểm tra tên type đã tồn tại chưa
    existing_type = db.query(models.Type).filter(models.Type.name == type.name).first()
    if existing_type:
        raise ValueError(f"Type với tên '{type.name}' đã tồn tại")
    
    # Tự động tạo slug từ name
    base_slug = create_slug_from_name(type.name)
    
    # Kiểm tra và tạo unique slug nếu cần
    unique_slug = generate_unique_slug(db, base_slug)
    
    print(f"Tạo type '{type.name}' với slug: '{unique_slug}'")
    
    db_type = models.Type(
        name=type.name,
        slug=unique_slug
    )
    
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def update_type(db: Session, id: str, type_update: schemas.TypeUpdate):
    db_type = get_type_by_id(db, id)
    if not db_type:
        raise ValueError(f"Type với id '{id}' không tồn tại")

    # Cập nhật tên type nếu có thay đổi
    if type_update.name and type_update.name != db_type.name:
        # Kiểm tra tên mới đã tồn tại chưa
        existing_type = db.query(models.Type).filter(models.Type.name == type_update.name).first()
        if existing_type and existing_type.slug != db_type.slug:
            raise ValueError(f"Type với tên '{type_update.name}' đã tồn tại")
        
        db_type.name = type_update.name
        
        # Tạo slug mới từ tên mới
        base_slug = create_slug_from_name(type_update.name)
        unique_slug = generate_unique_slug(db, base_slug)
        db_type.slug = unique_slug
    
    db.commit()
    db.refresh(db_type)
    return db_type

def delete_type(db: Session, id: str):
    db_type = get_type_by_id(db, id)
    if not db_type:
        raise ValueError(f"Type với id '{id}' không tồn tại")

    db.delete(db_type)
    db.commit()
    return db_type
