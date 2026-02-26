from .celery_app import celery_app
# This acts as the entrypoint module for imports pointing to `src.worker.tasks` previously
from .tasks.chat import generate_next_message_task
from .tasks.memory import consolidate_memories_task
from .tasks.discovery import agent_discover_task, agent_evaluate_likes_task
