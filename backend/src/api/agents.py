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
    return {"id": new_memory.id, "status": "added"}

@router.get("/{agent_id}/memories")
async def get_memories(agent_id: str, db: AsyncSession = Depends(get_db)):
    from src.models.domain import AgentMemory
    result = await db.execute(select(AgentMemory).where(AgentMemory.agent_id == agent_id).order_by(AgentMemory.created_at))
    return result.scalars().all()
