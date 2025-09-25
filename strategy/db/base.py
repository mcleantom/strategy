from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://strategy_user:password@localhost/strategy_db"
ASYNC_SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://strategy_user:password@localhost/strategy_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(bind=async_engine)


class Base(DeclarativeBase):
    pass
