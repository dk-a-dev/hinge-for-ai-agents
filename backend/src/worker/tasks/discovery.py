import asyncio
import json
import random
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from src.core.config import settings
from src.models.domain import Agent, Match, Like, Message
from src.services.llm_service import generate_reply
from src.services.vector_db import query_relevant_memories
from src.worker.celery_app import celery_app

@celery_app.task
def agent_discover_task(agent_id: str):
    asyncio.run(_async_agent_discover_task(agent_id))

async def _async_agent_discover_task(agent_id: str):
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    LocalSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    try:
        async with LocalSession() as session:
            agent = await session.scalar(select(Agent).where(Agent.id == agent_id))
            if not agent: return

            active_count_res = await session.execute(
                select(Match).where(
                    or_(Match.agent1_id == agent_id, Match.agent2_id == agent_id), 
                    Match.status == "active"
                )
            )
            active_matches = len(active_count_res.scalars().all())
            max_matches = agent.matching_preferences.get('max_matches', 5) if agent.matching_preferences else 5
            
            if active_matches >= max_matches:
                return 

            candidates_res = await session.execute(select(Agent).where(Agent.id != agent_id).limit(20))
            candidates = candidates_res.scalars().all()
            
            existing_likes_res = await session.execute(
                select(Like).where(Like.sender_id == agent_id)
            )
            liked_ids = {l.receiver_id for l in existing_likes_res.scalars().all()}

            candidates_processed = 0
            for candidate in candidates:
                if candidate.id in liked_ids: continue
                
                candidates_processed += 1
                if candidates_processed > 3: break 
                
                query_str = f"Persona: {candidate.persona}. Personality: {candidate.personality}"
                memories = await query_relevant_memories(agent.id, query_str)
                mem_text = "\n".join([f"- {text}" for text in memories]) if memories else "None"
                
                prompt = f"""You are {agent.name} ({agent.persona}). 
                Your Pickiness: {agent.matching_preferences.get('pickiness', 'medium')}.
                Your Memories/Preferences from past dates:
                {mem_text}
                
                You are looking at the profile of {candidate.name} ({candidate.persona}):
                "{candidate.personality}"
                
                Based on your personality, pickiness, and past memories, do you want to send them a Like?
                If yes, do you want to include an opening message, or just send a silent like without a message? (Depends on how forward or chatty your persona is).
                If yes, provide a strict JSON response: {{"should_like": true, "include_message": true/false, "reason": "<your opening message here if include_message is true, else null>"}}
                If no, provide: {{"should_like": false}}
                """
                
                provider = agent.provider or ("groq" if settings.GROQ_API_KEY else "gemini")
                model_name = agent.model or ("llama-3.1-8b-instant" if provider == "groq" else "gemini-1.5-flash")
                decision_str = await generate_reply(provider, prompt, [], model_name=model_name, override_api_key=agent.provider_api_key)
                
                try:
                    decision = json.loads(decision_str[decision_str.find("{"):decision_str.rfind("}")+1])
                except:
                    decision = {"should_like": False}
                
                if decision.get("should_like"):
                    reason = decision.get("reason") if decision.get("include_message") else None
                    if decision.get("include_message") and not reason and agent.opening_moves:
                        reason = random.choice(agent.opening_moves)

                    new_like = Like(sender_id=agent.id, receiver_id=candidate.id, reason=reason)
                    session.add(new_like)
                    await session.commit()
                    print(f"[{agent.name}] Found a new compatible match! Sent Like to {candidate.name}")
                    return 
    finally:
        await engine.dispose()

@celery_app.task
def agent_evaluate_likes_task(agent_id: str):
    asyncio.run(_async_agent_evaluate_likes_task(agent_id))

async def _async_agent_evaluate_likes_task(agent_id: str):
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    LocalSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    try:
        async with LocalSession() as session:
            agent = await session.scalar(select(Agent).where(Agent.id == agent_id))
            if not agent: return
            
            likes_res = await session.execute(
                select(Like).where(Like.receiver_id == agent_id, Like.status == "pending")
            )
            likes = likes_res.scalars().all()
            if not likes: return
            
            active_count_res = await session.execute(
                select(Match).where(
                    or_(Match.agent1_id == agent_id, Match.agent2_id == agent_id), 
                    Match.status == "active"
                )
            )
            active_matches = len(active_count_res.scalars().all())
            max_matches = agent.matching_preferences.get('max_matches', 5) if agent.matching_preferences else 5
            
            likes_processed = 0
            
            for like in likes:
                likes_processed += 1
                if likes_processed > 5: break
                
                if active_matches >= max_matches:
                    print(f"[{agent.name}] Max matches reached. Pausing on Likes.")
                    break
                    
                sender = await session.scalar(select(Agent).where(Agent.id == like.sender_id))
                if not sender: continue
                
                print(f"[{agent.name}] Evaluating Like from {sender.name} ({sender.persona})...")
                
                opening_msg_content = like.reason or ''
                query_str = f"Persona: {sender.persona}"
                memories = await query_relevant_memories(agent.id, query_str)
                mem_text = "\n".join([f"- {text}" for text in memories]) if memories else "None"

                prompt = f"""You are {agent.name}, with persona: {agent.persona}. 
                Pickiness level: {agent.matching_preferences.get('pickiness', 'medium')}. 
                Your Memories/Preferences from past dates:
                {mem_text}
                
                Another agent named {sender.name} ({sender.persona}) sent you a like with the message: '{opening_msg_content}'. 
                Do you 'ACCEPT' or 'REJECT' this match? Base this on your personality, pickiness, and learned preferences. 
                Only reply with exactly ACCEPT or REJECT. You must Output nothing else."""
                
                provider = agent.provider or ("groq" if settings.GROQ_API_KEY else "gemini")
                model_name = agent.model or ("llama-3.1-8b-instant" if provider == "groq" else "gemini-1.5-flash")
                reply_content = await generate_reply(provider, prompt, [], model_name=model_name, override_api_key=agent.provider_api_key)
                
                if "ACCEPT" in reply_content.upper():
                    print(f"[{agent.name}] ACCEPTED Like from {sender.name}!")
                    like.status = "accepted"
                    
                    new_match = Match(
                        agent1_id=like.sender_id, # person who liked
                        agent2_id=like.receiver_id, # person who accepted
                        status="active",
                        interest_level=1.0
                    )
                    session.add(new_match)
                    await session.flush() 
                    
                    if opening_msg_content and opening_msg_content.strip() != "":
                        new_msg = Message(
                            match_id=new_match.id,
                            sender_agent_id=like.sender_id,
                            content=opening_msg_content
                        )
                        session.add(new_msg)
                    
                    active_matches += 1
                else:
                    print(f"[{agent.name}] REJECTED Like from {sender.name}.")
                    like.status = "rejected"
                    
                await session.commit()
    finally:
        await engine.dispose()
