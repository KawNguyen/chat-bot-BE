from pydantic import BaseModel

class BrandBase(BaseModel):
    name: str

class BrandCreate(BrandBase):
    pass  # Chỉ có name, slug sẽ tự động tạo

class BrandUpdate(BrandBase):
    pass  # Có thể thêm các trường khác nếu cần

class BrandDelete(BaseModel):
    slug: str

class Brand(BrandBase):
    id: str
    slug: str 

    class Config:
        from_attributes = True