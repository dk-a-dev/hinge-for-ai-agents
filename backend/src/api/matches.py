from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from src.db.session import get_db
from src.models.domain import Match, Message, Like
from src.worker.tasks import generate_next_message_task

router = APIRouter()

class LikeCreate(BaseModel):
    sender_id: str
    receiver_id: str
    reason: Optional[str] = None

@router.post("/likes/")
async def send_like(like_data: LikeCreate, db: AsyncSession = Depends(get_db)):
    # Check if a like or match already exists
    stmt = select(Match).where(
        ((Match.agent1_id == like_data.sender_id) & (Match.agent2_id == like_data.receiver_id)) |
        ((Match.agent1_id == like_data.receiver_id) & (Match.agent2_id == like_data.sender_id))
    )
    res_match = await db.execute(stmt)
    if res_match.scalar_one_or_none():
        return {"status": "error", "message": "Match already exists"}
        
    stmt_like = select(Like).where(Like.sender_id == like_data.sender_id, Like.receiver_id == like_data.receiver_id)
    res_like = await db.execute(stmt_like)
    if res_like.scalar_one_or_none():
        return {"status": "error", "message": "Like already sent"}

    new_like = Like(sender_id=like_data.sender_id, receiver_id=like_data.receiver_id, reason=like_data.reason)
    db.add(new_like)
    await db.commit()
    return {"id": new_like.id, "status": "pending"}

@router.get("/likes/pending/{agent_id}")
async def get_pending_likes(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Like).where((Like.receiver_id == agent_id) & (Like.status == "pending")).order_by(Like.created_at))
    return result.scalars().all()

@router.put("/likes/{like_id}/accept")
async def accept_like(like_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Like).where(Like.id == like_id))
    like = result.scalar_one_or_none()
    if not like: return {"error": "Like not found"}
    
    like.status = "accepted"
    
    # Create the actual match now
    new_match = Match(agent1_id=like.sender_id, agent2_id=like.receiver_id, status="active")
    db.add(new_match)
    await db.commit()
    await db.refresh(new_match)

    if like.reason:
        first_msg = Message(
            match_id=new_match.id,
            sender_agent_id=like.sender_id,
            content=like.reason
        )
        db.add(first_msg)
        await db.commit()

    # Trigger agent2 to reply
    generate_next_message_task.apply_async(args=[new_match.id, new_match.agent2_id], countdown=2)
    return {"status": "active", "match_id": new_match.id}

@router.put("/likes/{like_id}/reject")
async def reject_like(like_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Like).where(Like.id == like_id))
    like = result.scalar_one_or_none()
    if not like: return {"error": "Like not found"}
    
    like.status = "rejected"
    await db.commit()
    return {"status": "rejected"}

@router.get("/active/{agent_id}")
async def get_active_matches(agent_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Match).where(
        ((Match.agent1_id == agent_id) | (Match.agent2_id == agent_id)) & 
        (Match.status == "active")
    ).order_by(Match.created_at)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{match_id}/messages")
async def get_match_messages(match_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Message).where(Message.match_id == match_id).order_by(Message.created_at))
    return result.scalars().all()

@router.put("/{match_id}/unmatch")
async def unmatch(match_id: str, repenting_agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match: return {"error": "Match not found"}
    
    match.status = "unmatched"
    await db.commit()
    return {"status": "unmatched"}
