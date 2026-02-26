import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from src.core.config import settings
from src.models.domain import Agent, Match, Like, Message, AgentMemory
from src.worker.celery_app import celery_app
from src.worker.tasks.chat import generate_next_message_task
from src.worker.tasks.discovery import agent_discover_task, agent_evaluate_likes_task
from src.worker.tasks.evaluation import agent_evaluate_matches_task
from src.worker.tasks.memory import consolidate_memories_task


engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
LocalSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@celery_app.task
def sweep_active_matches():
    """
    Periodic task (e.g. every 1 minute)
    Finds all active matches and decides if it's someone's turn to speak or evaluate.
    """
    asyncio.run(_async_sweep_active_matches())

async def _async_sweep_active_matches():
    async with LocalSession() as session:
        # Get all active matches
        matches_res = await session.execute(select(Match).where(Match.status == "active"))
        matches = matches_res.scalars().all()
        
        for match in matches:
            # Check length to see if we should trigger evaluation or just chat
            msgs_res = await session.execute(select(func.count(Message.id)).where(Message.match_id == match.id))
            msg_count = msgs_res.scalar()
            
            # If 4 or more messages, let's trigger an evaluation
            if msg_count > 0 and msg_count % 4 == 0:
                agent_evaluate_matches_task.apply_async(args=[match.agent1_id])
                agent_evaluate_matches_task.apply_async(args=[match.agent2_id])
            
            # Check whose turn it is
            last_msg_res = await session.execute(
                select(Message).where(Message.match_id == match.id).order_by(Message.created_at.desc()).limit(1)
            )
            last_msg = last_msg_res.scalar_one_or_none()
            
            if last_msg:
                # If agent 1 sent it, agent 2 should reply
                next_speaker_id = match.agent2_id if last_msg.sender_agent_id == match.agent1_id else match.agent1_id
            else:
                # No messages yet -> the person who "ACCEPTED" the like should speak first?
                # Actually typically the sender of a like speaks first if they left a comment.
                # If no comment, the matcher speaks first.
                next_speaker_id = match.agent2_id 
                
            generate_next_message_task.apply_async(args=[match.id, next_speaker_id])


@celery_app.task
def sweep_likes():
    """
    Periodic task (e.g. every 2 minutes)
    Finds agents with pending likes and queues them for evaluation.
    """
    asyncio.run(_async_sweep_likes())

async def _async_sweep_likes():
    async with LocalSession() as session:
        # Find distinct receivers who have pending likes
        receivers_res = await session.execute(
            select(Like.receiver_id).where(Like.status == "pending").distinct()
        )
        receiver_ids = receivers_res.scalars().all()
        
        for r_id in receiver_ids:
            agent_evaluate_likes_task.apply_async(args=[r_id])


@celery_app.task
def sweep_discovery():
    """
    Periodic task (e.g. every 2 minutes)
    Sweeps agents to trigger discovery mode if they have fewer than max_matches.
    """
    asyncio.run(_async_sweep_discovery())

async def _async_sweep_discovery():
    async with LocalSession() as session:
        agents_res = await session.execute(select(Agent.id))
        agent_ids = agents_res.scalars().all()
        for a_id in agent_ids:
            # We just queue it. The inner task checks max matches.
            agent_discover_task.apply_async(args=[a_id])


@celery_app.task
def sweep_memories():
    """
    Nightly task
    Consolidates agent memory rows into their personality profile.
    """
    asyncio.run(_async_sweep_memories())

async def _async_sweep_memories():
    async with LocalSession() as session:
        # Find agents who have 5 or more granular memories
        res = await session.execute(
            select(AgentMemory.agent_id)
            .group_by(AgentMemory.agent_id)
            .having(func.count(AgentMemory.id) >= 5)
        )
        agent_ids = res.scalars().all()
        
        for a_id in agent_ids:
            consolidate_memories_task.apply_async(args=[a_id])
