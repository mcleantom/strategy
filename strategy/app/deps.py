from strategy.db.base import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generator, Annotated
from fastapi import Depends


__all__ = [
    "SessionDep"
]


async def get_db() -> Generator:
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]
