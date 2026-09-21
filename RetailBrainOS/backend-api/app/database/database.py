from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


from collections.abc import Generator

def get_db() -> Generator:
    """
    Database session dependency.

    This generator will be used by future API dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()