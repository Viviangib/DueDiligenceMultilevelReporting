from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserLogin, Token
from db import SessionLocal
from controllers.user import create_user
from controllers.user import authenticate_user
from fastapi import HTTPException,status

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        create_user(db, user)
        return "User created sucessfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
   

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    token = authenticate_user(db, user)
    return {"access_token": token}
