from pydantic import BaseModel
from typing import Optional
from .brand import Brand as BrandSchema
from .type import Type as TypeSchema


class HeadphoneBase(BaseModel):
    name: str
    brand_id: Optional[str] = None
    type_id: Optional[str] = None
    price: int


class HeadphoneCreate(HeadphoneBase):
    pass  # Chỉ có name, brand_id, type_id, price; slug sẽ tự động tạo


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
        