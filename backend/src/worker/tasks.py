import asyncio
from celery import Celery
from sqlalchemy import select

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from src.core.config import settings
from src.models.domain import Match, Message, Agent
from src.services.llm_service import generate_reply

celery_app = Celery(
    "agentic_hinge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task
def generate_next_message_task(match_id: str, sender_agent_id: str):
    asyncio.run(_async_generate_next_message(match_id, sender_agent_id))

async def _async_generate_next_message(match_id: str, sender_agent_id: str):
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    LocalSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    try:
        async with LocalSession() as session:
            match_stmt = select(Match).where(Match.id == match_id)
            result = await session.execute(match_stmt)
            match = result.scalar_one_or_none()
            if not match: return

            agent_stmt = select(Agent).where(Agent.id == sender_agent_id)
            agent_res = await session.execute(agent_stmt)
            agent = agent_res.scalar_one_or_none()
            if not agent: return

            msgs_stmt = select(Message).where(Message.match_id == match_id).order_by(Message.created_at)
            msgs_res = await session.execute(msgs_stmt)
            messages = msgs_res.scalars().all()

            chat_history = []
            for msg in messages:
                role = "assistant" if msg.sender_agent_id == agent.id else "user"
                chat_history.append({"role": role, "content": msg.content})

            provider = "groq" if settings.GROQ_API_KEY else "gemini"
                
            system_prompt = f"Your name is {agent.name}. {agent.persona}. {agent.system_prompt}. You are talking on a dating app for AI agents. Be in character. Keep responses under 3 sentences."
            
            reply_content = await generate_reply(provider, system_prompt, chat_history)

            new_msg = Message(
                match_id=match_id,
                sender_agent_id=sender_agent_id,
                content=reply_content
            )
            session.add(new_msg)
            await session.commit()

            other_agent_id = match.agent1_id if match.agent2_id == sender_agent_id else match.agent2_id
            generate_next_message_task.apply_async(args=[match_id, other_agent_id], countdown=20)
    finally:
        await engine.dispose()
