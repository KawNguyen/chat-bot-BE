import database
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.headphone import Headphone, HeadphoneCreate, HeadphoneUpdate
from crud.headphone import get_headphones, create_headphone, get_headphone_by_slug

router = APIRouter(prefix="/headphones", tags=["Headphones"])

@router.get("/", response_model=list[Headphone])
def get_all_headphones(db: Session = Depends(database.get_db)):
    try:
        return get_headphones(db)
    except Exception as e:
        print(f"Error in get_all_headphones: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.get("/{slug}", response_model=Headphone)
def get_headphone_by_slug_endpoint(slug: str, db: Session = Depends(database.get_db)):
    headphone = get_headphone_by_slug(db, slug)
    if not headphone:
        raise HTTPException(status_code=404, detail="Headphone not found")
    return headphone

@router.post("/create", response_model=Headphone)
def create_new_headphone(headphone: HeadphoneCreate, db: Session = Depends(database.get_db)):
    try:
        return create_headphone(db, headphone)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in create_new_headphone: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@router.put("/update/{id}", response_model=Headphone)
def update_headphone_endpoint(id: str, headphone_update: HeadphoneUpdate, db: Session = Depends(database.get_db)):
    try:
        from crud.headphone import update_headphone
        return update_headphone(db, id, headphone_update)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in update_headphone_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/delete/{id}", response_model=Headphone)
def delete_headphone_endpoint(id: str, db: Session = Depends(database.get_db)):
    try:
        from crud.headphone import delete_headphone
        return delete_headphone(db, id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in delete_headphone_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    
