import asyncio
from celery import Celery
from src.core.config import settings
from celery.schedules import crontab

celery_app = Celery(
    "agentic_hinge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.worker.tasks.chat",
        "src.worker.tasks.memory",
        "src.worker.tasks.discovery",
        "src.worker.tasks.evaluation",
        "src.worker.scheduler"
    ]
)

celery_app.conf.beat_schedule = {
    # Every 30 seconds, trigger the sweep to look for matched agents missing messages
    "sweep-active-matches-30s": {
        "task": "src.worker.scheduler.sweep_active_matches",
        "schedule": 30.0,
    },
    # Every 60 seconds, trigger the sweep to look for agents with pending likes
    "sweep-likes-60s": {
        "task": "src.worker.scheduler.sweep_likes",
        "schedule": 60.0,
    },
    # Every 60 seconds, trigger the sweep to look for agents needing to discover
    "sweep-discovery-60s": {
        "task": "src.worker.scheduler.sweep_discovery",
        "schedule": 60.0,
    },
    # Nightly: consolidate memories for long term scaling
    "sweep-memories-nightly": {
        "task": "src.worker.scheduler.sweep_memories",
        "schedule": crontab(hour=1, minute=0),
    }
}
celery_app.conf.timezone = 'UTC'
