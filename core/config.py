from pydantic import SecretStr
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(".env")


class Settings(BaseSettings):
    SECRET_KEY: SecretStr = SecretStr("")
    OPENAI_API_KEY: SecretStr = SecretStr("")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    PINECONE_INDEX_NAME: str = ""
    DATABASE_URL: str = ""
    PINECONE_API_KEY: SecretStr = SecretStr("")
    PINECONE_NAMESPACE: str = ""
    REGION: str = "us-east-1"
    CLOUD: str = "aws"
    
    # SMTP Email Configuration
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: SecretStr = SecretStr("")
    SMTP_PASSWORD: SecretStr = SecretStr("")
    SMTP_REGION: str = ""
    SENDER_EMAIL: str = ""
    RECEIVER_EMAIL: str = ""
    
    # Frontend Configuration
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_FRONTEND_URLS: str = "http://localhost:5173"
    
    # Storage roots
    STORAGE_ROOT: str = "storage"
    UPLOADS_DIR: str = "uploads"
    VSS_UPLOADS_DIR: str = "vss_uploads"
    TEMP_UPLOADS_DIR: str = "temp_uploads"
    SUMMARY_REPORTS_DIR: str = "summary_reports"
    ANALYSIS_OUTPUT_DIR: str = "analysis"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


