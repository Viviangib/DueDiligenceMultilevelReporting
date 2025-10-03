from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserLogin,Token
from db import SessionLocal
from controllers.user import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/signup", status_code=201)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    create_user(db, user)
    return {"message": "User created successfully"}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    token = authenticate_user(db, user)

    response = JSONResponse(
        content={"access_token": token, "token_type": "bearer"}
    )
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,   
        secure=True,     
        samesite="None"  
    )

    return response


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="auth_token",
        path="/",
        httponly=True,
        secure=True,
        samesite="none"
    )
    return {"message": "Logged out"}
