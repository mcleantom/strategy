from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from strategy.db.base import AsyncSessionLocal

__all__ = ["SessionDep"]


async def get_db() -> Generator:
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]
