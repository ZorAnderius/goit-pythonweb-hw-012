"""
Utility Endpoints.

This module provides utility endpoints for the application, including a health checker
to verify the database connection status.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db

router = APIRouter(tags=["utils"])

@router.get("/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Perform a health check to verify database connectivity.

    This endpoint executes a simple SQL query to check if the database is
    configured and operational. If the check fails, it returns an HTTP 500 error.

    :param db: Database session dependency.
    :return: A dictionary with a "Healthy" message if the database connection is successful.
    :raises HTTPException: If the database is not configured correctly or cannot be reached.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.scalar_one_or_none()

        if result is None:
            raise HTTPException(
                status_code=500, 
                detail="Database is not configured correctly"
            )
        return {"message": "Healthy"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, 
            detail="Error connecting to the database"
        )
