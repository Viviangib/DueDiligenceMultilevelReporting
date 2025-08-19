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


