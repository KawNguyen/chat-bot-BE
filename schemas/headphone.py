from pydantic import BaseModel, Field, field_validator
from typing import Optional
from .brand import Brand as BrandSchema
from .type import Type as TypeSchema
import re
import unicodedata


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


class HeadphoneBase(BaseModel):
    name: str
    brand_slug: Optional[str] = Field(None, description="Slug hoặc tên của brand")
    type_slug: Optional[str] = Field(None, description="Slug hoặc tên của type")
    price: int
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tên headphone"""
        if not v or not v.strip():
            raise ValueError("Tên headphone không được để trống")
        
        # Kiểm tra xem tên có thể tạo slug hợp lệ không
        slug = create_slug_from_name(v)
        if not slug:
            raise ValueError(f"Tên '{v}' không hợp lệ. Tên phải chứa ít nhất một ký tự chữ hoặc số.")
        
        return v.strip()


class HeadphoneCreate(HeadphoneBase):
    pass  # AI sẽ gửi brand_slug và type_slug, CRUD tự động chuyển thành UUID


class HeadphoneUpdate(HeadphoneBase):
    pass  # Có thể thêm các trường khác nếu cần


class HeadphoneDelete(BaseModel):
    slug: str


class Headphone(HeadphoneBase):
    id: str
    slug: str
    brand: Optional[BrandSchema] = None
    type: Optional[TypeSchema] = None

    class Config:
        from_attributes = True
        