from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def get_engine(db_url: str | None = None):
    url = db_url or "postgresql://strategy_user:password@localhost/strategy_db"
    return create_engine(url)


def get_session_maker(db_url: str | None = None):
    engine = get_engine(db_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_async_engine(db_url: str | None = None):
    url = db_url or "postgresql+asyncpg://strategy_user:password@localhost/strategy_db"
    return create_async_engine(url)


def get_async_session_maker(db_url: str | None = None):
    engine = get_async_engine(db_url)
    return async_sessionmaker(bind=engine)


SessionLocal = get_session_maker()
AsyncSessionLocal = get_async_session_maker()
