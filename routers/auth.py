from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserLogin,Token, PasswordResetRequest, PasswordReset
from db import SessionLocal
from controllers.user import create_user, authenticate_user, request_password_reset, reset_password
from core.config import settings
import os

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


@router.post("/request-password-reset")
def request_password_reset_route(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    sender_email = os.getenv("SENDER_EMAIL", "no-reply@example.com")
    aws_region = os.getenv("AWS_REGION", settings.REGION)
    aws_access_key = os.getenv("AWS_ACCESS_KEY")
    aws_secret_key = os.getenv("AWS_SECRET_KEY")

    return request_password_reset(
        db=db,
        email=payload.email,
        frontend_url=frontend_url,
        sender_email=sender_email,
        aws_region=aws_region,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
    )


@router.post("/reset-password")
def reset_password_route(payload: PasswordReset, db: Session = Depends(get_db)):
    return reset_password(db=db, token=payload.token, new_password=payload.password)
