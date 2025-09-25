from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .backtest import backtest_router
from .candles import candles_router
from .exchanges import exchanges_router
from .strategies import strategies_router

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(exchanges_router)
app.include_router(candles_router)
app.include_router(backtest_router)
app.include_router(strategies_router)
