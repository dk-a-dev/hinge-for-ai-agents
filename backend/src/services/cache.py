import json
from typing import Optional, Dict, Any
import redis
import redis.asyncio as redis_async
from src.core.config import settings

# Async client for FastAPI operations (caching)
redis_client = redis_async.from_url(settings.REDIS_URL, decode_responses=True)

# Sync client for Celery workers to publish events
redis_sync_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def publish_event(channel: str, event_type: str, data: Dict[str, Any]):
    """Synchronously publishes a payload to a Redis PubSub channel. 
       Usually called from blocking Celery tasks."""
    payload = {
        "type": event_type,
        "data": data
    }
    redis_sync_client.publish(channel, json.dumps(payload))


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
