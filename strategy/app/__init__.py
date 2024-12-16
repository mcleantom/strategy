from fastapi import FastAPI
from .exchanges import exchanges_router

app = FastAPI()
app.include_router(exchanges_router)
