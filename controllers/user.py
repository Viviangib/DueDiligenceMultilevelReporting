from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.user import User
from models.password_reset_token import PasswordResetToken
from schemas.user import UserCreate, UserLogin
from utils.security import get_password_hash, verify_password, create_access_token
from pydantic import EmailStr
import uuid
import boto3
from botocore.exceptions import ClientError
import os
from pydantic import EmailStr


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


def request_password_reset(db: Session, email: EmailStr, frontend_url: str, sender_email: str, aws_region: str, aws_access_key: str | None = None, aws_secret_key: str | None = None):
    # Always respond success to prevent user enumeration
    user = get_user_by_email(db, email)
    if not user:
        return {"message": "If an account exists with that email, we have sent a password reset link"}

    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    db_token = PasswordResetToken(email=email, token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    reset_link = f"{frontend_url.rstrip('/')}/reset-password?token={token}"

    ses_client = boto3.client(
        "ses",
        region_name=aws_region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
    )

    subject = "Password Reset Request"
    body_text = f"Use the following link to reset your password: {reset_link}"
    body_html = f"<p>Use the following link to reset your password:</p><p><a href=\"{reset_link}\">Reset Password</a></p>"

    try:
        ses_client.send_email(
            Destination={"ToAddresses": [email]},
            Message={
                "Body": {
                    "Html": {"Charset": "UTF-8", "Data": body_html},
                    "Text": {"Charset": "UTF-8", "Data": body_text},
                },
                "Subject": {"Charset": "UTF-8", "Data": subject},
            },
            Source=sender_email,
        )
    except ClientError as e:
        # Do not leak SES errors to user; log and continue
        print(f"SES send_email error: {e}")

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
