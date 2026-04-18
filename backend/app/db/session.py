from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _build_engine_kwargs() -> dict:
    """
    Build engine kwargs. When routing through PgBouncer in transaction mode,
    asyncpg prepared statement caching must be disabled (cache is per-connection
    and cannot be shared across pooled connections in transaction mode).
    """
    kwargs: dict = {
        "echo": False,
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": settings.db_pool_timeout,
        "pool_recycle": settings.db_pool_recycle,
        "pool_pre_ping": True,
    }
    if settings.db_pgbouncer_mode:
        # Disable asyncpg statement cache; SQLAlchemy picks this up via connect_args
        kwargs["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        }
    return kwargs


engine = create_async_engine(settings.database_url, **_build_engine_kwargs())
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
