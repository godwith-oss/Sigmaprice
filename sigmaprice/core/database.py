"""Database connection utilities"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sigmaprice.core.config import get_database_url
from typing import Generator

_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
    return _engine


def get_session_factory():
    """Get session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    return _SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def create_session() -> Session:
    """Create a new database session (non-generator version)."""
    factory = get_session_factory()
    return factory()


def close_engine():
    """Close database engine (for cleanup)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
    _SessionLocal = None