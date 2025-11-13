import database
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.type import Type, TypeCreate, TypeUpdate
from crud.type import get_types, create_type, get_type_by_slug, update_type, delete_type

router = APIRouter(prefix="/types", tags=["Types"])

@router.get("/", response_model=list[Type])
def get_all_types(db: Session = Depends(database.get_db)):
    try:
        return get_types(db)
    except Exception as e:
        print(f"Error in get_all_types: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.get("/{slug}", response_model=Type)
def get_type_by_slug_endpoint(slug: str, db: Session = Depends(database.get_db)):
    type_ = get_type_by_slug(db, slug)
    if not type_:
        raise HTTPException(status_code=404, detail="Type not found")
    return type_

@router.post("/create", response_model=Type)
def create_new_type(type_: TypeCreate, db: Session = Depends(database.get_db)):
    try:
        return create_type(db, type_)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in create_new_type: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/update/{id}", response_model=Type)
def update_type_endpoint(id: str, type_update: TypeUpdate, db: Session = Depends(database.get_db)):
    try:
        return update_type(db, id, type_update)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in update_type_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/delete/{id}", response_model=Type)
def delete_type_endpoint(id: str, db: Session = Depends(database.get_db)):
    try:
        return delete_type(db, id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in delete_type_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")