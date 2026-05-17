from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings

split_engine = create_async_engine(settings.SPLIT_DATABASE_URL, echo=False)
SplitSessionFactory = async_sessionmaker(split_engine, class_=AsyncSession, expire_on_commit=False)