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
    import logging
    from urllib.parse import urlparse
    
    logger = logging.getLogger(__name__)
    
    # Get frontend URL from settings (environment variable)
    frontend_url = settings.FRONTEND_URL
    allowed_urls = settings.ALLOWED_FRONTEND_URLS.split(',')
    
    # Validate frontend URL
    if frontend_url not in allowed_urls:
        logger.warning(f"⚠️ Frontend URL '{frontend_url}' not in allowed list: {allowed_urls}")
        # Use the first allowed URL as fallback
        frontend_url = allowed_urls[0].strip()
        logger.info(f"🔄 Using fallback frontend URL: {frontend_url}")
    
    logger.info(f"🚀 Password reset API called for email: {payload.email}")
    logger.info(f"   Frontend URL: {frontend_url}")
    logger.info(f"   Allowed URLs: {allowed_urls}")

    result = request_password_reset(
        db=db,
        email=payload.email,
        frontend_url=frontend_url,
    )
    
    logger.info(f"📤 Password reset API response: {result}")
    return result


@router.post("/reset-password")
def reset_password_route(payload: PasswordReset, db: Session = Depends(get_db)):
    return reset_password(db=db, token=payload.token, new_password=payload.password)
