from sqlalchemy.orm import Session, joinedload
import models
from schemas import headphone as schemas
from .brand import get_brand_by_slug, get_brand_by_name
from .type import get_type_by_slug, get_type_by_name
import re
import unicodedata

def get_headphones(db: Session):
    return db.query(models.Headphone).options(joinedload(models.Headphone.brand), joinedload(models.Headphone.type)).all()

def get_headphone_by_slug(db: Session, slug: str):
    return db.query(models.Headphone).options(joinedload(models.Headphone.brand), joinedload(models.Headphone.type)).filter(models.Headphone.slug == slug).first()

def get_headphone_by_id(db: Session, id: str):
    return db.query(models.Headphone).options(joinedload(models.Headphone.brand), joinedload(models.Headphone.type)).filter(models.Headphone.id == id).first()

def create_slug_from_name(name: str) -> str:
    """Tạo slug từ tên, xử lý ký tự tiếng Việt có dấu"""
    if not name or not name.strip():
        return ""
    
    slug = name.lower().strip()
    
    # Chuyển đổi ký tự có dấu thành không dấu
    slug = unicodedata.normalize('NFD', slug)
    slug = slug.encode('ascii', 'ignore').decode('utf-8')
    
    # Thay thế khoảng trắng và underscore bằng dấu gạch ngang
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Chỉ giữ lại chữ cái, số và dấu gạch ngang
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # Loại bỏ dấu gạch ngang liên tiếp
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

def resolve_brand_id(db: Session, brand_identifier: str) -> str:
    """Chuyển đổi slug hoặc UUID thành UUID của brand"""
    if not brand_identifier:
        return None
    
    # Nếu là UUID (có dấu - và dài), trả về luôn
    if "-" in brand_identifier and len(brand_identifier) > 30:
        return brand_identifier
    
    # Nếu là slug, tìm brand theo slug
    brand = get_brand_by_slug(db, brand_identifier)
    if brand:
        return brand.id
    
    # Fallback: tìm theo name
    brand = get_brand_by_name(db, brand_identifier)
    if brand:
        return brand.id
    
    return None

def resolve_type_id(db: Session, type_identifier: str) -> str:
    """Chuyển đổi slug hoặc UUID thành UUID của type"""
    if not type_identifier:
        return None
    
    # Nếu là UUID (có dấu - và dài), trả về luôn
    if "-" in type_identifier and len(type_identifier) > 30:
        return type_identifier
    
    # Nếu là slug, tìm type theo slug
    type_obj = get_type_by_slug(db, type_identifier)
    if type_obj:
        return type_obj.id
    
    # Fallback: tìm theo name
    type_obj = get_type_by_name(db, type_identifier)
    if type_obj:
        return type_obj.id
    
    return None

def create_headphone(db: Session, headphone: schemas.HeadphoneCreate):
    existing_headphone = db.query(models.Headphone).filter(models.Headphone.name == headphone.name).first()
    if existing_headphone:
        raise ValueError(f"Tai nghe với tên '{headphone.name}' đã tồn tại")
    
    # Validate brand_slug và type_slug không được null hoặc rỗng
    if not headphone.brand_slug or not headphone.brand_slug.strip():
        raise ValueError("Brand là bắt buộc. Vui lòng cung cấp brand_slug.")
    
    if not headphone.type_slug or not headphone.type_slug.strip():
        raise ValueError("Type là bắt buộc. Vui lòng cung cấp type_slug.")
    
    # Chuyển đổi brand_slug và type_slug từ slug/name sang UUID
    brand_uuid = resolve_brand_id(db, headphone.brand_slug)
    if not brand_uuid:
        raise ValueError(f"Không tìm thấy brand '{headphone.brand_slug}'. Vui lòng kiểm tra lại.")
    
    type_uuid = resolve_type_id(db, headphone.type_slug)
    if not type_uuid:
        raise ValueError(f"Không tìm thấy type '{headphone.type_slug}'. Vui lòng kiểm tra lại.")
    
    base_slug = create_slug_from_name(headphone.name)
    if not base_slug:
        raise ValueError(f"Không thể tạo slug từ tên '{headphone.name}'. Tên phải chứa ít nhất một ký tự hợp lệ.")
    
    unique_slug = generate_unique_slug(db, base_slug)
    
    print(f"Tạo tai nghe '{headphone.name}' với slug: '{unique_slug}', brand: {brand_uuid}, type: {type_uuid}")
    
    db_headphone = models.Headphone(
        name=headphone.name,
        brand_id=brand_uuid,
        type_id=type_uuid,
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

def create_headphones_bulk(db: Session, headphones: list[schemas.HeadphoneCreate]):
    """Tạo nhiều headphones cùng lúc"""
    created_headphones = []
    errors = []
    
    for headphone in headphones:
        try:
            # Kiểm tra tên headphone đã tồn tại chưa
            existing_headphone = db.query(models.Headphone).filter(models.Headphone.name == headphone.name).first()
            if existing_headphone:
                errors.append(f"Tai nghe '{headphone.name}' đã tồn tại")
                continue
            
            # Chuyển đổi brand_slug và type_slug từ slug/name sang UUID
            brand_uuid = resolve_brand_id(db, headphone.brand_slug)
            type_uuid = resolve_type_id(db, headphone.type_slug)
            
            # Validate UUID sau khi chuyển đổi
            if headphone.brand_slug and not brand_uuid:
                errors.append(f"Không tìm thấy brand '{headphone.brand_slug}' cho tai nghe '{headphone.name}'")
                continue
            
            if headphone.type_slug and not type_uuid:
                errors.append(f"Không tìm thấy type '{headphone.type_slug}' cho tai nghe '{headphone.name}'")
                continue
            
            # Tự động tạo slug từ name
            base_slug = create_slug_from_name(headphone.name)
            if not base_slug:
                errors.append(f"Không thể tạo slug từ tên '{headphone.name}'. Tên phải chứa ít nhất một ký tự hợp lệ.")
                continue
            
            unique_slug = generate_unique_slug(db, base_slug)
            
            db_headphone = models.Headphone(
                name=headphone.name,
                brand_id=brand_uuid,
                type_id=type_uuid,
                price=headphone.price,
                slug=unique_slug
            )
            
            db.add(db_headphone)
            db.flush()  # Flush để lấy ID nhưng chưa commit
            created_headphones.append(db_headphone)
            print(f"Tạo tai nghe '{headphone.name}' với slug: '{unique_slug}', brand: {brand_uuid}, type: {type_uuid}")
            
        except Exception as e:
            errors.append(f"Lỗi tạo tai nghe '{headphone.name}': {str(e)}")
            db.rollback()  # Rollback lỗi của item này
            # Tạo session mới để tiếp tục
            continue
    
    if created_headphones:
        try:
            db.commit()
            for headphone in created_headphones:
                db.refresh(headphone)
        except Exception as e:
            db.rollback()
            errors.append(f"Lỗi commit: {str(e)}")
            return [], errors
    
    return created_headphones, errors

def delete_headphone(db: Session, id: str):
    db_headphone = get_headphone_by_id(db, id)
    if not db_headphone:
        raise ValueError(f"Tai nghe với id '{id}' không tồn tại")

    db.delete(db_headphone)
    db.commit()
    print(f"Đã xóa tai nghe với id: '{id}'")
    return db_headphone
