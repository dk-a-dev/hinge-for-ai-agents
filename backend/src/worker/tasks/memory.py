import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from src.core.config import settings
from src.models.domain import Agent, AgentMemory
from src.services.llm_service import generate_reply
from src.services.vector_db import delete_memory_embeddings, upsert_agent_embedding
from src.worker.celery_app import celery_app

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
                delete_memory_embeddings([m.id for m in memories])
                
                # Delete old memories from SQL DB
                for m in memories:
                    await session.delete(m)
                    
                # Re-embed the agent's new overall persona context
                combined_text = f"Persona: {agent.persona}. Personality: {agent.personality}. Instructions: {agent.system_prompt}"
                try:
                    await asyncio.to_thread(upsert_agent_embedding, agent.id, combined_text)
                except Exception:
                    pass
                
                await session.commit()
                print(f"[{agent.name}] Successfully consolidated memories into new personality!")
    finally:
        await engine.dispose()
