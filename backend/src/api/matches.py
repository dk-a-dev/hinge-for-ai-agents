from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.db.session import get_db
from src.models.domain import Match, Message
from src.worker.tasks import generate_next_message_task

router = APIRouter()

class MatchCreate(BaseModel):
    agent1_id: str
    agent2_id: str

@router.post("/")
async def create_match(match_data: MatchCreate, db: AsyncSession = Depends(get_db)):
    new_match = Match(agent1_id=match_data.agent1_id, agent2_id=match_data.agent2_id)
    db.add(new_match)
    await db.commit()
    await db.refresh(new_match)

    # Initial icebreaker from agent1
    first_msg = Message(
        match_id=new_match.id,
        sender_agent_id=match_data.agent1_id,
        content="Hey, I think we matched! What's your vibe?"
    )
    db.add(first_msg)
    await db.commit()

    # Trigger agent2 to reply to the icebreaker using Celery
    generate_next_message_task.apply_async(args=[new_match.id, match_data.agent2_id], countdown=2)

    return {"id": new_match.id, "status": new_match.status}

@router.get("/")
async def list_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match))
    matches = result.scalars().all()
    return matches

@router.get("/{match_id}/messages")
async def get_match_messages(match_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Message).where(Message.match_id == match_id).order_by(Message.created_at))
    messages = result.scalars().all()
    return messages
