from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.db.session import get_db
from src.models.domain import Agent
from src.services.vector_db import upsert_agent_embedding, query_compatible_agents_by_id

router = APIRouter()

class AgentCreate(BaseModel):
    name: str
    persona: str
    personality: str
    system_prompt: str

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
