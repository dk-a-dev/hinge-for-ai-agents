from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from src.db.session import get_db
from src.models.domain import Match, Message, Like, Agent

router = APIRouter()

@router.get("/")
async def get_activity_feed(limit: int = 50, db: AsyncSession = Depends(get_db)):
    # Fetch agents to create a lookup map
    agents_stmt = select(Agent.id, Agent.name)
    agents_res = await db.execute(agents_stmt)
    agent_map = {row.id: row.name for row in agents_res}
    
    activities = []

    # Fetch recent messages
    msgs_stmt = select(Message).order_by(desc(Message.created_at)).limit(limit)
    msgs_res = await db.execute(msgs_stmt)
    for msg in msgs_res.scalars():
        activities.append({
            "type": "message",
            "id": msg.id,
            "agent_name": agent_map.get(msg.sender_agent_id, "Unknown"),
            "agent_id": msg.sender_agent_id,
            "match_id": msg.match_id,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None
        })

    # Fetch recent matches
    matches_stmt = select(Match).order_by(desc(Match.created_at)).limit(limit)
    matches_res = await db.execute(matches_stmt)
    for match in matches_res.scalars():
        activities.append({
            "type": "match",
            "id": match.id,
            "agent1_name": agent_map.get(match.agent1_id, "Unknown"),
            "agent2_name": agent_map.get(match.agent2_id, "Unknown"),
            "agent1_id": match.agent1_id,
            "agent2_id": match.agent2_id,
            "compatibility_score": match.compatibility_score,
            "status": match.status,
            "timestamp": match.created_at.isoformat() if match.created_at else None
        })
        
    # Fetch recent likes
    likes_stmt = select(Like).order_by(desc(Like.created_at)).limit(limit)
    likes_res = await db.execute(likes_stmt)
    for like in likes_res.scalars():
        activities.append({
            "type": "like",
            "id": like.id,
            "sender_name": agent_map.get(like.sender_id, "Unknown"),
            "receiver_name": agent_map.get(like.receiver_id, "Unknown"),
            "sender_id": like.sender_id,
            "receiver_id": like.receiver_id,
            "status": like.status,
            "timestamp": like.created_at.isoformat() if like.created_at else None
        })

    # Sort activities by timestamp descending
    activities.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "", reverse=True)
    
    return activities[:limit]
