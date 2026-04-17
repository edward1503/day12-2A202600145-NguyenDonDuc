import time
import redis
from fastapi import HTTPException
from app.config import settings

# Initialize Redis client
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

def check_rate_limit(user_id: str):
    """
    Sliding window rate limiter using Redis ZSET.
    Ensures statelessness across multiple app instances.
    """
    now = time.time()
    key = f"rate_limit:{user_id}"
    window_seconds = 60
    
    try:
        # Create pipeline for atomicity
        pipe = redis_client.pipeline()
        # Remove old requests
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        # Count current requests
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiry for cleanup
        pipe.expire(key, window_seconds + 1)
        
        # Execute
        _, request_count, _, _ = pipe.execute()
        
        if request_count >= settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                headers={"Retry-After": "60"},
            )
    except redis.RedisError as e:
        # Fallback logic or log error
        pass
