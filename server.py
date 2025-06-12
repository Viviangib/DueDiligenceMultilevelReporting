from fastapi import FastAPI
from routers  import auth
from db import Base, engine

app = FastAPI()

# Create DB tables
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(auth.router)