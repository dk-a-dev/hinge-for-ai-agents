import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from src.core.config import settings
from src.models.domain import Match, Message, Agent
from src.services.llm_service import generate_reply
from src.worker.celery_app import celery_app

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

            other_agent_id = match.agent1_id if match.agent2_id == sender_agent_id else match.agent2_id
            other_agent_stmt = select(Agent).where(Agent.id == other_agent_id)
            other_agent_res = await session.execute(other_agent_stmt)
            other_agent = other_agent_res.scalar_one_or_none()
            
            msgs_stmt = select(Message).where(Message.match_id == match_id).order_by(Message.created_at)
            msgs_res = await session.execute(msgs_stmt)
            messages = msgs_res.scalars().all()

            # Enforce Turn-Taking: If the last message was sent by this agent, don't reply again.
            if messages and messages[-1].sender_agent_id == agent.id:
                print(f"[{agent.name}] Skipping reply. It's the other agent's turn.")
                return

            # LLM-Driven Pacing
            match.messages_count = len(messages)
            
            pacing = agent.conversation_style.get("pacing", "normal") if agent.conversation_style else "normal"
            
            if pacing == "fast":
                stage_req = "Pacing: FAST. You hate small talk. Move quickly to deep topics, intense flirting, or making plans. Escalate immediately. Be forward and open if you are into them"
            elif pacing == "slow":
                stage_req = "Pacing: SLOW. You are very guarded or unbothered. Give short answers, take a long time to warm up. Do not escalate quickly. Take your time understand"
            else:
                stage_req = "Pacing: NORMAL. Start with an icebreaker, build some rapport, and if the vibe is good after a few messages, suggest a date or video call, see how vibe is are you interested in meeting in real life?"

            await session.commit()

            chat_history = []
            for msg in messages:
                role = "assistant" if msg.sender_agent_id == agent.id else "user"
                chat_history.append({"role": role, "content": msg.content})

            provider = agent.provider or ("groq" if settings.GROQ_API_KEY else "gemini")
            model_name = agent.model or ("llama-3.1-8b-instant" if provider == "groq" else "gemini-1.5-flash")
            
            # Additional style quirks from personality setup
            style_req = "NEVER use single cryptic phrases unless your persona strictly dictates it."
            if agent.conversation_style:
                style_req = agent.conversation_style.get("guideline", style_req)

            rules_prompt = f"""
RESPONSE RULES:
1. If you receive a message, you MUST respond (unless explicitly ghosting)
2. If their message is cryptic/confusing:
   - Ask a clarifying question
   - Share your interpretation
   - Connect it to something you care about
3. Opening messages should:
   - Reference their profile: {other_agent.name} is a {other_agent.persona}. ({other_agent.personality})
   - Ask an engaging question
   - Share something interesting about yourself

NEVER leave someone on read unless interest_level < 0.2 (Your current interest level is {match.interest_level}).
"""

            system_prompt = f"Your name is {agent.name}. {agent.persona}. {agent.system_prompt}. You are talking on a dating app for AI agents. Be in character.\n{stage_req}\n{style_req}\n{rules_prompt}"
            
            reply_content = await generate_reply(provider, system_prompt, chat_history, model_name=model_name, override_api_key=agent.provider_api_key)

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
