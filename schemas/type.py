from pydantic import BaseModel

class TypeBase(BaseModel):
    name: str

class TypeCreate(TypeBase):
    pass  # Chỉ có name, slug sẽ tự động tạo

class TypeUpdate(TypeBase):
    pass  # Có thể thêm các trường khác nếu cần

class TypeDelete(BaseModel):
    slug: str

class Type(TypeBase):
    id: str
    slug: str 

    class Config:
        from_attributes = True