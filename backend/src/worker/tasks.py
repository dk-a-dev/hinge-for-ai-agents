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

@celery_app.task
def consolidate_memories_task(agent_id: str):
    asyncio.run(_async_consolidate_memories(agent_id))

async def _async_consolidate_memories(agent_id: str):
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    LocalSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    try:
        async with LocalSession() as session:
            agent_res = await session.execute(select(Agent).where(Agent.id == agent_id))
            agent = agent_res.scalar_one_or_none()
            if not agent: return
            
            from src.models.domain import AgentMemory
            mems_res = await session.execute(select(AgentMemory).where(AgentMemory.agent_id == agent_id))
            memories = mems_res.scalars().all()
            
            if len(memories) < 5:
                # Not enough memories to warrant a consolidation run
                return
                
            mem_text = "\n".join([f"- {m.memory_type}: {m.content}" for m in memories])
            
            prompt = f"""You are analyzing the dating history for {agent.name} ({agent.persona}).
            Current Personality: "{agent.personality}"
            
            They have learned the following new things from recent dates:
            {mem_text}
            
            Please rewrite their 'Personality' to incorporate these new learnings fluidly.
            Keep it under 3 sentences. Output ONLY the new personality string, no quotes or prefix."""
            
            new_personality = await generate_reply(
                agent.provider or "groq", 
                prompt, [], 
                model_name=agent.model or "llama-3.1-8b-instant", 
                override_api_key=agent.provider_api_key
            )
            if new_personality and len(new_personality) > 10:
                agent.personality = new_personality.strip('"\'')
                
                # Delete old memories from vector DB
                from src.services.vector_db import delete_memory_embeddings, upsert_agent_embedding
                delete_memory_embeddings([m.id for m in memories])
                
                # Delete old memories from SQL DB
                for m in memories:
                    await session.delete(m)
                    
                # Re-embed the agent's new overall persona context
                combined_text = f"Persona: {agent.persona}. Personality: {agent.personality}. Instructions: {agent.system_prompt}"
                try:
                    import asyncio
                    await asyncio.to_thread(upsert_agent_embedding, agent.id, combined_text)
                except Exception:
                    pass
                
                await session.commit()
                print(f"[{agent.name}] Successfully consolidated memories into new personality!")
    finally:
        await engine.dispose()
