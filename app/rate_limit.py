from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.config import settings
from app.redis_client import get_redis


async def limit_login_attempts(request: Request, redis: Redis = Depends(get_redis)) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:login:{client_ip}"


    async with redis.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, settings.login_rate_limit_window_seconds, nx=True)
        attempts, _ = await pipe.execute()

    if attempts > settings.login_rate_limit_attempts:
        retry_after = await redis.ttl(key)
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many attempts",
                            headers={"Retry-After": str(max(retry_after, 1))},
                            )