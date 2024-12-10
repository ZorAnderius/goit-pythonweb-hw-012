"""
Database Session Management.

This module provides utilities for managing database sessions using SQLAlchemy 
with support for asynchronous operations.
"""

import contextlib
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker

from src.conf.config import settings

class DatabaseSessionManager:
    """
    Manages the lifecycle of database sessions.

    This class is responsible for creating and managing asynchronous database 
    sessions using SQLAlchemy.

    Attributes:
        _engine (AsyncEngine | None): The database engine for asynchronous operations.
        _session_maker (async_sessionmaker): The session factory bound to the engine.
    """
    def __init__(self, url: str):
        """
        Initialize the DatabaseSessionManager.

        Args:
            url (str): The database connection URL.
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Provide a database session.

        This method creates an asynchronous database session using the session factory 
        and ensures proper cleanup by closing the session after use.

        Yields:
            AsyncSession: A SQLAlchemy asynchronous session.

        Raises:
            Exception: If the session maker is not initialized.
            SQLAlchemyError: If an error occurs during session operations.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise  # Re-raise the original error
        finally:
            await session.close()


# Global session manager instance for the application
sessionmanager = DatabaseSessionManager(settings.DB_URL)

async def get_db():
    """
    Dependency for retrieving a database session.

    This function provides a database session to FastAPI endpoints 
    via dependency injection.

    Yields:
        AsyncSession: A SQLAlchemy asynchronous session.
    """
    async with sessionmanager.session() as session:
        yield session
