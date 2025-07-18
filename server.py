import logging
from fastapi import FastAPI
from routers import api_router
from db import Base, engine
from config import settings

logger = logging.getLogger(__name__)


# Log Pinecone namespace on startup
def log_pinecone_namespace():
    logger.info(
        f"Pinecone namespace selected from config: {settings.PINECONE_NAMESPACE}"
    )


# If using FastAPI, add startup event
app = FastAPI()


@app.on_event("startup")
def startup_event():
    log_pinecone_namespace()


# Create DB tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(api_router)
