from sqlalchemy.orm import Session
import models
from schemas import brand as schemas
import re

def get_brands(db: Session):
    return db.query(models.Brand).all()

def get_brand_by_id(db: Session, brand_id: str):
    return db.query(models.Brand).filter(models.Brand.id == brand_id).first()

def get_brand_by_slug(db: Session, slug: str):
    return db.query(models.Brand).filter(models.Brand.slug == slug).first()

def get_brand_by_name(db: Session, name: str):
    """Tìm brand theo tên (case-insensitive)"""
    return db.query(models.Brand).filter(models.Brand.name.ilike(name)).first()

def check_slug_available(db: Session, slug: str) -> bool:
    """Kiểm tra slug có available không"""
    return get_brand_by_slug(db, slug) is None

def create_slug_from_name(name: str) -> str:
    """Tạo slug từ tên brand"""
    # Chuyển về lowercase và thay thế spaces/special chars bằng dấu gạch ngang
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def generate_unique_slug(db: Session, base_slug: str) -> str:
    """Tạo slug unique bằng cách thêm số suffix nếu cần"""
    original_slug = base_slug
    counter = 1
    
    while get_brand_by_slug(db, base_slug):
        base_slug = f"{original_slug}-{counter}"
        counter += 1
    
    return base_slug

def create_brand(db: Session, brand: schemas.BrandCreate):
    # Kiểm tra tên brand đã tồn tại chưa
    existing_brand = db.query(models.Brand).filter(models.Brand.name == brand.name).first()
    if existing_brand:
        raise ValueError(f"Brand với tên '{brand.name}' đã tồn tại")
    
    # Tự động tạo slug từ name
    base_slug = create_slug_from_name(brand.name)
    
    # Kiểm tra và tạo unique slug nếu cần
    unique_slug = generate_unique_slug(db, base_slug)
    
    print(f"Tạo brand '{brand.name}' với slug: '{unique_slug}'")
    
    db_brand = models.Brand(
        name=brand.name,
        slug=unique_slug
    )
    
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return db_brand

def update_brand(db: Session, brand_id: str, brand_update: schemas.BrandUpdate):
    db_brand = get_brand_by_id(db, brand_id)
    if not db_brand:
        raise ValueError(f"Brand với ID '{brand_id}' không tồn tại")
    
    # Cập nhật tên brand nếu có thay đổi
    if brand_update.name and brand_update.name != db_brand.name:
        # Kiểm tra tên mới đã tồn tại chưa
        existing_brand = db.query(models.Brand).filter(models.Brand.name == brand_update.name).first()
        if existing_brand and existing_brand.id != brand_id:
            raise ValueError(f"Brand với tên '{brand_update.name}' đã tồn tại")
        
        db_brand.name = brand_update.name
        
        # Tạo slug mới từ tên mới
        base_slug = create_slug_from_name(brand_update.name)
        unique_slug = generate_unique_slug(db, base_slug)
        db_brand.slug = unique_slug
        print(f"Cập nhật brand '{brand_update.name}' với slug mới: '{unique_slug}'")
    
    db.commit()
    db.refresh(db_brand)
    return db_brand

def create_brands_bulk(db: Session, brands: list[schemas.BrandCreate]):
    """Tạo nhiều brands cùng lúc"""
    created_brands = []
    errors = []
    
    for brand in brands:
        try:
            # Kiểm tra tên brand đã tồn tại chưa
            existing_brand = db.query(models.Brand).filter(models.Brand.name == brand.name).first()
            if existing_brand:
                errors.append(f"Brand '{brand.name}' đã tồn tại")
                continue
            
            # Tự động tạo slug từ name
            base_slug = create_slug_from_name(brand.name)
            unique_slug = generate_unique_slug(db, base_slug)
            
            db_brand = models.Brand(
                name=brand.name,
                slug=unique_slug
            )
            
            db.add(db_brand)
            db.flush()  # Flush để lấy ID nhưng chưa commit
            created_brands.append(db_brand)
            print(f"Tạo brand '{brand.name}' với slug: '{unique_slug}'")
            
        except Exception as e:
            errors.append(f"Lỗi tạo brand '{brand.name}': {str(e)}")
    
    if created_brands:
        db.commit()
        for brand in created_brands:
            db.refresh(brand)
    
    return created_brands, errors

def delete_brand(db: Session, brand_id: str):
    db_brand = get_brand_by_id(db, brand_id)
    if not db_brand:
        raise ValueError(f"Brand với ID '{brand_id}' không tồn tại")

    db.delete(db_brand)
    db.commit()
    print(f"Đã xóa brand với ID: '{brand_id}'")
    return db_brand