from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.user import User
from models.password_reset_token import PasswordResetToken
from schemas.user import UserCreate, UserLogin
from utils.security import get_password_hash, verify_password, create_access_token
from pydantic import EmailStr
import uuid
import logging
from services.email import email_service

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: EmailStr):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username, email=user.email, hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, login_data: UserLogin):
    user = get_user_by_email(db, login_data.email)
    if not user or not verify_password(login_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=120)
    )


def request_password_reset(db: Session, email: EmailStr, frontend_url: str):
    logger.info(f"Password reset requested for email: {email}")
    
    # Explicitly validate that the email exists; avoid sending emails to unknown addresses
    user = get_user_by_email(db, email)
    if not user:
        logger.warning(f"Password reset requested for non-existent email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email does not exist"
        )

    logger.info(f"User found for email: {email}, generating reset token")
    
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    logger.info(f"Generated token: {token[:8]}... (expires at: {expires_at})")

    db_token = PasswordResetToken(email=email, token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    logger.info(f"Reset token saved to database with ID: {db_token.id}")

    reset_link = f"{frontend_url.rstrip('/')}/reset-password?token={token}"
    logger.info(f"Generated reset link: {reset_link}")

    # Send email using SMTP
    logger.info(f"Attempting to send password reset email to: {email}")
    try:
        success = email_service.send_password_reset_email(
            to_email=email,
            reset_link=reset_link
        )
        if success:
            logger.info(f"✅ Password reset email sent successfully to: {email}")
        else:
            logger.error(f"❌ Failed to send password reset email to {email}")
    except Exception as e:
        # Do not leak email errors to user; log and continue
        logger.error(f"❌ Email send error for {email}: {str(e)}", exc_info=True)

    return {"message": "If an account exists with that email, we have sent a password reset link"}


def reset_password(db: Session, token: str, new_password: str):
    token_row: PasswordResetToken | None = (
        db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
    )

    if not token_row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    if token_row.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reset token has already been used")
    if datetime.now(timezone.utc) > token_row.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has expired")

    user = get_user_by_email(db, token_row.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user.hashed_password = get_password_hash(new_password)
    token_row.used = True

    db.add(user)
    db.add(token_row)
    db.commit()

    return {"message": "Password has been successfully reset"}
