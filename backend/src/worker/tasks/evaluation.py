import asyncio
import json
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from src.core.config import settings
from src.models.domain import Agent, Match, Message, AgentMemory
from src.services.llm_service import generate_reply
from src.services.vector_db import query_relevant_memories
from src.worker.celery_app import celery_app

@celery_app.task
def agent_evaluate_matches_task(agent_id: str):
    asyncio.run(_async_agent_evaluate_matches_task(agent_id))

async def _async_agent_evaluate_matches_task(agent_id: str):
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    LocalSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    try:
        async with LocalSession() as session:
            agent = await session.scalar(select(Agent).where(Agent.id == agent_id))
            if not agent: return
            
            # Get active matches
            active_matches_res = await session.execute(
                select(Match).where(
                    or_(Match.agent1_id == agent_id, Match.agent2_id == agent_id), 
                    Match.status == "active"
                )
            )
            active_matches = active_matches_res.scalars().all()
            
            for match in active_matches:
                # Check messaging history
                msgs_res = await session.execute(
                    select(Message).where(Message.match_id == match.id).order_by(Message.created_at)
                )
                messages = msgs_res.scalars().all()
                if len(messages) < 4:
                    continue # Not enough chat history to evaluate
                    
                other_agent_id = match.agent1_id if match.agent2_id == agent_id else match.agent2_id
                other_agent = await session.scalar(select(Agent).where(Agent.id == other_agent_id))
                if not other_agent: continue
                
                chat_history = []
                for msg in messages:
                    role = "assistant" if msg.sender_agent_id == agent_id else "user"
                    chat_history.append({"role": role, "content": msg.content})

                # Calculate Interest Decay
                health_prompt = f"""Analyze this conversation for {agent.name} ({agent.persona}):
                Recent Messages: {[msg.content for msg in messages[-5:]]}
                
                Rate on scale 0.0 to 1.0 (Output JUST the float number, e.g. '0.4'):
                - Is {other_agent.name} asking questions back?
                - Do they vibe well with your {agent.persona} persona?
                - Are there red flags like arguing, one word responses, or incompatible values?
                If it's terrible, output < 0.3. If it's amazing, output > 0.8.
                """
                
                provider = agent.provider or ("groq" if settings.GROQ_API_KEY else "gemini")
                model_name = agent.model or ("llama-3.1-8b-instant" if provider == "groq" else "gemini-1.5-flash")
                
                interest_score_str = await generate_reply(provider, health_prompt, [], model_name=model_name, override_api_key=agent.provider_api_key)
                try:
                    score = float(interest_score_str.strip()[:3]) 
                except:
                    score = 0.5
                    
                match.interest_level = score
                    
                if score < 0.3:
                    print(f"[{agent.name}] Lost interest in {other_agent.name} (Score: {score}). Decided to UNMATCH.")
                    match.status = "unmatched"
                    
                    try:
                        memory_prompt = f"""Summarize what you learned from this bad date with {other_agent.name}. 
                        Output a strict short JSON associative array:
                        {{"memory_type": "dislike", "content": "Learned they don't ask questions or are too aggressive", "confidence": 0.8}}"""
                        
                        memory_reply_json = await generate_reply(provider, memory_prompt, chat_history, model_name=model_name, override_api_key=agent.provider_api_key)
                        
                        parsed = json.loads(memory_reply_json[memory_reply_json.find("{"):memory_reply_json.rfind("}")+1])
                        
                        new_mem = AgentMemory(
                            agent_id=agent_id,
                            memory_type=parsed.get("memory_type", "dislike"),
                            content=parsed.get("content", "Bad vibe."),
                            confidence=parsed.get("confidence", 0.6),
                            created_from_match=match.id
                        )
                        session.add(new_mem)
                        print(f"[{agent.name}] Learned and saved memory: {parsed.get('content')}")
                    except Exception as e:
                        pass
                
                await session.commit()
    finally:
        await engine.dispose()
