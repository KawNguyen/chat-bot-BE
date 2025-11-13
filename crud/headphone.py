from sqlalchemy.orm import Session, joinedload
import models
from schemas import headphone as schemas
import re

def get_headphones(db: Session):
    return db.query(models.Headphone).options(joinedload(models.Headphone.brand), joinedload(models.Headphone.type)).all()

def get_headphone_by_slug(db: Session, slug: str):
    return db.query(models.Headphone).options(joinedload(models.Headphone.brand), joinedload(models.Headphone.type)).filter(models.Headphone.slug == slug).first()

def get_headphone_by_id(db: Session, id: str):
    return db.query(models.Headphone).options(joinedload(models.Headphone.brand), joinedload(models.Headphone.type)).filter(models.Headphone.id == id).first()

def create_slug_from_name(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-{2,}', '-', slug).strip('-')
    return slug

def generate_unique_slug(db: Session, base_slug: str) -> str:
    """Tạo slug unique bằng cách thêm số suffix nếu cần"""
    original_slug = base_slug
    counter = 1
    
    while get_headphone_by_slug(db, base_slug):
        base_slug = f"{original_slug}-{counter}"
        counter += 1
    
    return base_slug

def create_headphone(db: Session, headphone: schemas.HeadphoneCreate):
    existing_headphone = db.query(models.Headphone).filter(models.Headphone.name == headphone.name).first()
    if existing_headphone:
        raise ValueError(f"Tai nghe với tên '{headphone.name}' đã tồn tại")
    
    base_slug = create_slug_from_name(headphone.name)
    
    unique_slug = generate_unique_slug(db, base_slug)
    
    print(f"Tạo tai nghe '{headphone.name}' với slug: '{unique_slug}'")
    
    db_headphone = models.Headphone(
        name=headphone.name,
        brand_id=headphone.brand_id,
        type_id=headphone.type_id,
        price=headphone.price,
        slug=unique_slug
    )
    
    db.add(db_headphone)
    db.commit()
    db.refresh(db_headphone)
    return db_headphone

def update_headphone(db: Session, id: str, headphone_update: schemas.HeadphoneUpdate):
    db_headphone = get_headphone_by_id(db, id)
    if not db_headphone:
        raise ValueError(f"Tai nghe với id '{id}' không tồn tại")

    if headphone_update.name and headphone_update.name != db_headphone.name:
        existing_headphone = db.query(models.Headphone).filter(models.Headphone.name == headphone_update.name).first()
        if existing_headphone and existing_headphone.slug != db_headphone.slug:
            raise ValueError(f"Tai nghe với tên '{headphone_update.name}' đã tồn tại")
        
        db_headphone.name = headphone_update.name
        
        # Tạo slug mới từ tên mới
        base_slug = create_slug_from_name(headphone_update.name)
        unique_slug = generate_unique_slug(db, base_slug)
        db_headphone.slug = unique_slug
    
    # Cập nhật các trường khác
    db_headphone.brand_id = headphone_update.brand_id
    db_headphone.type_id = headphone_update.type_id
    db_headphone.price = headphone_update.price
    
    db.commit()
    db.refresh(db_headphone)
    return db_headphone

def delete_headphone(db: Session, id: str):
    db_headphone = get_headphone_by_id(db, id)
    if not db_headphone:
        raise ValueError(f"Tai nghe với id '{id}' không tồn tại")

    db.delete(db_headphone)
    db.commit()
    print(f"Đã xóa tai nghe với id: '{id}'")
    return db_headphone
