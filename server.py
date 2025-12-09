import os
# Set tokenizers parallelism before any imports that use tokenizers
# This prevents warnings when processes are forked after tokenizers initialization
os.environ["TOKENIZERS_PARALLELISM"] = "true"

import warnings
# Suppress PyTorch FutureWarning about encoder_attention_mask
warnings.filterwarnings("ignore", category=FutureWarning, message=".*encoder_attention_mask.*")
# Suppress LangChain import warning
warnings.filterwarnings("ignore", message=".*Importing debug from langchain root module.*")
# Suppress LangChain deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import api_router
from db import Base, engine
from core.config import settings
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
    
# Create DB tables
Base.metadata.create_all(bind=engine)
# Register routes
app.include_router(api_router)
