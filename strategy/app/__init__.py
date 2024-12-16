from fastapi import FastAPI
from .exchanges import exchanges_router
from .candles import candles_router

app = FastAPI()
app.include_router(exchanges_router)
app.include_router(candles_router)
