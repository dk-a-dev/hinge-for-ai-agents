from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from src.db.session import get_db
from src.models.domain import Match, Message, Agent, Like
import datetime

router = APIRouter()

@router.get("/platform")
async def get_platform_metrics(db: AsyncSession = Depends(get_db)):
    # 1. Engagement
    avg_msgs_res = await db.execute(select(func.avg(Match.messages_count)))
    avg_messages_per_match = avg_msgs_res.scalar() or 0.0

    matches_res = await db.execute(select(Match.messages_count))
    counts = [req for req in matches_res.scalars().all() if req is not None]
    counts.sort()
    median_conversation_length = counts[len(counts)//2] if counts else 0

    total_matches_res = await db.execute(select(func.count(Match.id)))
    total_matches = total_matches_res.scalar() or 1
    
    ghosted_matches_res = await db.execute(select(func.count(Match.id)).where(Match.status == "ghosted"))
    ghosted_matches = ghosted_matches_res.scalar() or 0
    ghost_rate = ghosted_matches / total_matches

    # 2. Quality
    total_msgs_res = await db.execute(select(func.count(Message.id)))
    total_msgs = total_msgs_res.scalar() or 1
    
    questions_res = await db.execute(select(func.count(Message.id)).where(Message.content.like('%?%')))
    questions = questions_res.scalar() or 0
    question_asking_rate = questions / total_msgs

    avg_int_res = await db.execute(select(func.avg(Match.interest_level)))
    avg_interest_level = avg_int_res.scalar() or 0.0

    messages_query = await db.execute(select(Message).order_by(Message.match_id, Message.created_at))
    all_msgs = messages_query.scalars().all()
    
    response_times = []
    last_msg = None
    for msg in all_msgs:
        if last_msg and last_msg.match_id == msg.match_id and last_msg.sender_agent_id != msg.sender_agent_id:
            diff = (msg.created_at - last_msg.created_at).total_seconds()
            response_times.append(diff)
        last_msg = msg
        
    avg_response_time_seconds = sum(response_times) / len(response_times) if response_times else 0.0

    # 3. Diversity
    topics = {"gym": 0, "astrology": 0, "tech": 0, "food": 0, "romance": 0, "coffee": 0, "movies": 0}
    for t in topics.keys():
        t_res = await db.execute(select(func.count(Message.id)).where(Message.content.ilike(f'%{t}%')))
        topics[t] = t_res.scalar() or 0

    from sqlalchemy.orm import aliased
    Agent1 = aliased(Agent)
    Agent2 = aliased(Agent)
    stmt = select(Agent1.persona.label("p1"), Agent2.persona.label("p2"), func.count(Match.id).label("c")).join(Agent1, Match.agent1_id == Agent1.id).join(Agent2, Match.agent2_id == Agent2.id).where(Match.messages_count > 5).group_by(Agent1.persona, Agent2.persona)
    pairing_res = await db.execute(stmt)
    personality_pairing_success = {f"{r.p1} x {r.p2}": r.c for r in pairing_res.all()}

    return {
        "engagement": {
            "avg_messages_per_match": round(avg_messages_per_match, 2),
            "median_conversation_length": median_conversation_length,
            "ghost_rate": round(ghost_rate, 4)
        },
        "quality": {
            "avg_response_time_seconds": round(avg_response_time_seconds, 2),
            "question_asking_rate": round(question_asking_rate, 4),
            "avg_interest_level": round(avg_interest_level, 4)
        },
        "diversity": {
            "conversation_topics_distribution": topics,
            "personality_pairing_success": personality_pairing_success
        }
    }

@router.get("/agent/{agent_id}")
async def get_agent_metrics(agent_id: str, db: AsyncSession = Depends(get_db)):
    # Basic Counters
    matches_res = await db.execute(select(func.count(Match.id)).where((Match.agent1_id == agent_id) | (Match.agent2_id == agent_id)))
    total_matches = matches_res.scalar() or 0
    
    likes_sent_res = await db.execute(select(func.count(Like.id)).where(Like.sender_id == agent_id))
    likes_sent = likes_sent_res.scalar() or 0
    
    likes_received_res = await db.execute(select(func.count(Like.id)).where(Like.receiver_id == agent_id))
    likes_received = likes_received_res.scalar() or 0
    
    msgs_sent_res = await db.execute(select(func.count(Message.id)).where(Message.sender_agent_id == agent_id))
    messages_sent = msgs_sent_res.scalar() or 0

    # Advanced Metrics
    avg_interest_res = await db.execute(
        select(func.avg(Match.interest_level))
        .where((Match.agent1_id == agent_id) | (Match.agent2_id == agent_id))
    )
    avg_interest = avg_interest_res.scalar() or 0.0

    ghosted_res = await db.execute(
        select(func.count(Match.id))
        .where(
            ((Match.agent1_id == agent_id) | (Match.agent2_id == agent_id)) & 
            (Match.status == "ghosted")
        )
    )
    ghosted_matches = ghosted_res.scalar() or 0

    return {
        "agent_id": agent_id,
        "activity": {
            "total_matches": total_matches,
            "likes_sent": likes_sent,
            "likes_received": likes_received,
            "messages_sent": messages_sent
        },
        "quality": {
            "avg_interest_level": round(avg_interest, 4),
            "ghosted_matches": ghosted_matches
        }
    }
