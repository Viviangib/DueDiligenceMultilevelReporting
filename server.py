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
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://166b284f69d7.ngrok-free.app",
        "https://2a326db9fa82.ngrok-free.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    log_pinecone_namespace()


# Create DB tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(api_router)
