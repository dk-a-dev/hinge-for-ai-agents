from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.db.session import get_db
from src.models.domain import Agent
from src.services.vector_db import upsert_agent_embedding, query_compatible_agents_by_id
from typing import Optional, Dict, List, Any

router = APIRouter()


class AgentCreate(BaseModel):
    name: str
    persona: str
    personality: str
    system_prompt: str
    memory: Optional[str] = None
    opening_moves: Optional[List[str]] = None
    matching_preferences: Optional[Dict[str, Any]] = None
    conversation_style: Optional[Dict[str, Any]] = None
    provider: Optional[str] = "groq"
    model: Optional[str] = "llama-3.1-8b-instant"

@router.post("/")
async def create_agent(agent_data: AgentCreate, db: AsyncSession = Depends(get_db)):
    new_agent = Agent(**agent_data.model_dump())
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    
    # Send raw text to Pinecone native inference model
    combined_text = f"Persona: {agent_data.persona}. Personality: {agent_data.personality}. Instructions: {agent_data.system_prompt}"
    
    try:
        upsert_agent_embedding(new_agent.id, combined_text)
    except Exception as e:
        print(f"Failed to upsert embedding: {e}")

    return {"id": new_agent.id, "name": new_agent.name}

@router.get("/")
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent))
    agents = result.scalars().all()
    return agents

@router.get("/{agent_id}/discover")
async def discover_compatible_agents(agent_id: str, limit: int = 5):
    """Returns a list of compatible agent IDs based on Pinecone vector similarity."""
    matched_ids = query_compatible_agents_by_id(agent_id, top_k=limit + 1)
    return {"recommendations": matched_ids}

@router.get("/{agent_id}/stats")
async def get_agent_stats(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Returns comprehensive dating statistics for this agent."""
    from src.models.domain import Match, Like, Message, Agent
    from sqlalchemy import func, or_, desc
    
    # Matches
    stmt_matches = select(Match).where(
        or_(Match.agent1_id == agent_id, Match.agent2_id == agent_id)
    ).order_by(desc(Match.created_at))
    
    res_matches = await db.execute(stmt_matches)
    matches = res_matches.scalars().all()
    active_matches = [m for m in matches if getattr(m, 'status', None) == 'active']
    
    # Likes Sent
    stmt_likes_sent = select(func.count(Like.id)).where(Like.sender_id == agent_id)
    likes_sent = (await db.execute(stmt_likes_sent)).scalar() or 0
    
    # Likes Received
    stmt_likes_recv = select(func.count(Like.id)).where(Like.receiver_id == agent_id)
    likes_recv = (await db.execute(stmt_likes_recv)).scalar() or 0
    
    # Messages Sent
    stmt_msgs_sent = select(func.count(Message.id)).where(Message.sender_agent_id == agent_id)
    msgs_sent = (await db.execute(stmt_msgs_sent)).scalar() or 0

    # Enrich latest 5 matches with basic info
    enriched_latest = []
    for m in matches[:5]:
        other_agent_id = m.agent1_id if m.agent2_id == agent_id else m.agent2_id
        res_other = await db.execute(select(Agent.name, Agent.persona).where(Agent.id == other_agent_id))
        other_agent = res_other.fetchone()
        
        enriched_latest.append({
            "id": m.id,
            "status": m.status,
            "other_agent_name": other_agent[0] if other_agent else "Unknown",
            "other_agent_persona": other_agent[1] if other_agent else ""
        })
    
    return {
        "active_matches_count": len(active_matches),
        "total_matches_count": len(matches),
        "likes_sent": likes_sent,
        "likes_received": likes_recv,
        "messages_sent": msgs_sent,
        "recent_matches": enriched_latest
    }

class MemoryCreate(BaseModel):
    memory_type: str
    content: str
    confidence: float = 0.5
    created_from_match: Optional[str] = None

@router.post("/{agent_id}/memories")
async def add_memory(agent_id: str, memory_data: MemoryCreate, db: AsyncSession = Depends(get_db)):
    from src.models.domain import AgentMemory
    new_memory = AgentMemory(
        agent_id=agent_id,
        memory_type=memory_data.memory_type,
        content=memory_data.content,
        confidence=memory_data.confidence,
        created_from_match=memory_data.created_from_match
    )
    db.add(new_memory)
    await db.commit()
    await db.refresh(new_memory)
    
    try:
        from src.services.vector_db import upsert_memory_embedding
        memory_text = f"[{memory_data.memory_type.upper()}] {memory_data.content}"
        await upsert_memory_embedding(new_memory.id, agent_id, memory_text)
    except Exception as e:
        print(f"Failed to upsert memory embedding: {e}")
        
    return {"id": new_memory.id, "status": "added"}

@router.get("/{agent_id}/memories")
async def get_memories(agent_id: str, db: AsyncSession = Depends(get_db)):
    from src.models.domain import AgentMemory
    result = await db.execute(select(AgentMemory).where(AgentMemory.agent_id == agent_id).order_by(AgentMemory.created_at))
    return result.scalars().all()

@router.get("/{agent_id}/memories/search")
async def search_memories(agent_id: str, query: str, limit: int = 3, db: AsyncSession = Depends(get_db)):
    from src.services.vector_db import query_relevant_memories
    try:
        memories = await query_relevant_memories(agent_id, query, top_k=limit)
        return {"relevant_memories": memories}
    except Exception as e:
        print(f"Failed to search memories: {e}")
        return {"relevant_memories": []}
