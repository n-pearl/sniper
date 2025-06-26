from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pgvector.sqlalchemy import Vector
from config import settings
import logging

logger = logging.getLogger(__name__)

# Database URL for async operations
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


async def init_db():
    """Initialize database with extensions and tables"""
    async with async_engine.begin() as conn:
        # Enable required extensions
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Create hypertable for time-series data
        await conn.execute(text("""
            SELECT create_hypertable('news_articles', 'published_at', 
                                   if_not_exists => TRUE, 
                                   migrate_data => TRUE)
        """))
        
        # Create indexes for vector search
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_news_sentiment_vector 
            ON news_articles USING ivfflat (sentiment_vector vector_cosine_ops)
            WITH (lists = 100)
        """))
        
        # Create indexes for time-based queries
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_news_published_at 
            ON news_articles (published_at DESC)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_news_ticker 
            ON news_articles (ticker_symbol)
        """))


async def get_async_db():
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    """Dependency to get sync database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
