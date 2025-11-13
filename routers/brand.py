import database
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.brand import Brand, BrandCreate, BrandUpdate
from crud.brand import get_brands, create_brand, get_brand_by_slug, get_brand_by_id, update_brand, delete_brand

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("/", response_model=list[Brand])
def get_all_brands(db: Session = Depends(database.get_db)):
    try:
        return get_brands(db)
    except Exception as e:
        print(f"Error in get_all_brands: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{slug}", response_model=Brand)
def get_brand_by_slug_endpoint(slug: str, db: Session = Depends(database.get_db)):
    brand = get_brand_by_slug(db, slug)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.post("/create", response_model=Brand)
def create_new_brand(brand: BrandCreate, db: Session = Depends(database.get_db)):
    try:
        return create_brand(db, brand)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in create_new_brand: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.get("/id/{brand_id}", response_model=Brand)
def get_brand_by_id_endpoint(brand_id: str, db: Session = Depends(database.get_db)):
    brand = get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.put("/update/{brand_id}", response_model=Brand)
def update_brand_endpoint(brand_id: str, brand_update: BrandUpdate, db: Session = Depends(database.get_db)):
    try:
        return update_brand(db, brand_id, brand_update)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in update_brand_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.delete("/delete/{brand_id}")
def delete_brand_endpoint(brand_id: str, db: Session = Depends(database.get_db)):
    try:
        return delete_brand(db, brand_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in delete_brand_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")