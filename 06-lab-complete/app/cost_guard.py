# hãy di chuyển tới branch MASTER
import time
import redis
import logging
import json
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

def check_and_record_cost(input_tokens: int, output_tokens: int):
    """
    Tracks daily cost using Redis to ensure persistence across instances.
    Blocks requests if the daily budget is exceeded.
    """
    today = time.strftime("%Y-%m-%d")
    key = f"daily_cost:{today}"
    
    # Simple pricing model (example)
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    
    try:
        current_cost = float(redis_client.get(key) or 0.0)
        
        if current_cost >= settings.daily_budget_usd:
            logger.warning(json.dumps({"event": "budget_exhausted", "cost": current_cost, "limit": settings.daily_budget_usd}))
            raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
        
        # Increment cost and set expiry for cleanup (2 days)
        redis_client.incrbyfloat(key, cost)
        redis_client.expire(key, 172800) 
        
    except redis.RedisError as e:
        logger.error(f"Redis cost guard error: {e}")
        pass
