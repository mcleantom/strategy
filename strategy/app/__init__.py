from fastapi import FastAPI
from .exchanges import exchanges_router
from .candles import candles_router
from .backtest import run_strategy_router
from .strategies import strategies_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(exchanges_router)
app.include_router(candles_router)
app.include_router(run_strategy_router)
app.include_router(strategies_router)
