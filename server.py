import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import api_router
from db import Base, engine
from core.config import settings
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


# Log Pinecone namespace on startup
def log_pinecone_namespace():
    logger.info(
        f"Pinecone namespace selected from config: {settings.PINECONE_NAMESPACE}"
    )


# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ddmr.gib-foundation.org",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    log_pinecone_namespace()
    
    # Ensure required directories exist
    vss_dir = os.path.join(settings.STORAGE_ROOT, settings.VSS_UPLOADS_DIR)
    os.makedirs(vss_dir, exist_ok=True)
    logger.info(f"Ensured VSS uploads directory exists: {vss_dir}")


# Create DB tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(api_router)
