from fastapi import FastAPI
from routers import api_router
from db import Base, engine

app = FastAPI()

# Create DB tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(api_router)