from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import settings
import json

async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
    pool_size=15,
    max_overflow=25,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False)
)

AsyncSessionFactory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session


class Base(DeclarativeBase):
    pass



