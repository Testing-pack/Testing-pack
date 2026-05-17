from .database import SplitSessionFactory
from sqlalchemy.ext.asyncio import AsyncSession

async def get_split_db() -> AsyncSession:
    async with SplitSessionFactory() as session:
        yield session