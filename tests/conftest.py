from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable, Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from strategy.db.base import Base
from strategy.db.candle import CandleModel


@pytest.fixture(scope="session")  # type: ignore[misc]
def postgres_container() -> Generator[PostgresContainer]:
    """Fixture to provide a PostgreSQL container for testing."""
    with PostgresContainer("postgres:17-alpine") as postgres:
        yield postgres


@pytest.fixture  # type: ignore[misc]
def db_connection(postgres_container: PostgresContainer) -> str:
    """Fixture to provide a database connection string."""
    return str(postgres_container.get_connection_url(driver="asyncpg"))


@pytest.fixture  # type: ignore[misc]
async def db_engine(db_connection: str) -> AsyncGenerator[AsyncEngine]:
    """Fixture to provide a database engine."""
    engine = create_async_engine(db_connection, echo=False)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture  # type: ignore[misc]
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Fixture to provide a database session."""
    async with AsyncSession(db_engine) as session:
        yield session


@pytest.fixture(autouse=True)  # type: ignore[misc]
async def run_migrations(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture  # type: ignore[misc]
def exchange() -> str:
    return "alpaca"


@pytest.fixture  # type: ignore[misc]
def symbol() -> str:
    return "AAPL"


@pytest.fixture  # type: ignore[misc]
def save_candles(
    db_session: AsyncSession,
) -> Callable[[list[CandleModel]], Awaitable[None]]:
    """Fixture to save candles to the database."""

    async def _save_candles(candles: list[CandleModel]) -> None:
        async with db_session.begin():
            db_session.add_all(candles)
        await db_session.commit()

    return _save_candles
