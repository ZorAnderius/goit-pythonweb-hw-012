"""
Redis Connection Module.

This module manages the connection to the Redis server, providing an asynchronous 
function to access a shared Redis client instance.
"""

import redis.asyncio as redis
from src.conf.config import settings

# Global variable to store the Redis client instance
redis_variable = None

async def get_redis_variable():
    """
    Get the Redis client instance.

    This function initializes and returns a global Redis client instance. 
    If the instance is not already initialized, it creates a new one using 
    the settings defined in the application configuration.

    Returns:
        redis.Redis: An asynchronous Redis client instance.
    """
    global redis_variable
    if redis_variable is None:
        redis_variable = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            decode_responses=True
        )
    return redis_variable
