import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import api_router
from db import Base, engine
from core.config import settings

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
        "http://localhost:5173",  # Local frontend
        "https://359239a9f80f.ngrok-free.app",  # Current ngrok frontend URL
        "https://e932bc683e0c.ngrok-free.app",  # Current ngrok backend URL
        "https://*.ngrok-free.app",  # Allow any ngrok subdomain
        "https://*.ngrok.io",  # Allow any ngrok.io subdomain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    log_pinecone_namespace()


# Create DB tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(api_router)
