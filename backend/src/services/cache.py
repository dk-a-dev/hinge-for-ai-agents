import json
from typing import Optional, Dict, Any
import redis.asyncio as redis
from src.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def set_cached_agent(agent_id: str, agent_data: Dict[str, Any], expire_seconds: int = 3600):
    """Caches an agent's full profile data in Redis for fast cross-process access."""
    await redis_client.setex(
        f"agent_profile:{agent_id}",
        expire_seconds,
        json.dumps(agent_data)
    )

async def get_cached_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an agent's full profile data from Redis if it exists."""
    data = await redis_client.get(f"agent_profile:{agent_id}")
    if data:
        return json.loads(data)
    return None

async def invalidate_cached_agent(agent_id: str):
    """Deletes an agent's profile from the Redis cache."""
    await redis_client.delete(f"agent_profile:{agent_id}")
