import redis.asyncio as redis
from src.conf.config import settings

redis_variable = None

async def get_redis_variable():
    global redis_variable
    if redis_variable is None:
        redis_variable = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
        )
    return redis_variable