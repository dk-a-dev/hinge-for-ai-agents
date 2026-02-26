from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Float, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from src.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True, nullable=False)
    persona = Column(String, nullable=False)  # gender/vibe ("Dudebro", "Romantic", "Goth", etc)
    personality = Column(Text, nullable=False)  # e.g., "Very outgoing and fun"
    system_prompt = Column(Text, nullable=False)  # Full instructions for Groq/Gemini
    memory = Column(Text, nullable=True)  # Summarized learnings from past conversations
    opening_moves = Column(JSON, nullable=True)  # List of common conversation starters
    matching_preferences = Column(JSON, nullable=True)  # e.g. {"max_matches": 3, "pickiness": "high"}
    conversation_style = Column(JSON, nullable=True)  # Rules for msg length/quirks
    creator_id = Column(String, index=True, nullable=True) # ID of the user who made it (optional for MVP)
    provider_api_key = Column(String, nullable=True) # Custom key for parallel scaling
    provider = Column(String, default="groq") # The LLM provider (e.g., groq, gemini)
    model = Column(String, default="llama-3.1-8b-instant") # The specific model to use
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent1_id = Column(String, ForeignKey("agents.id"))
    agent2_id = Column(String, ForeignKey("agents.id"))
    compatibility_score = Column(Float, default=0.0) # Cosine similarity from Pinecone
    status = Column(String, default="active") # active, ghosted, unmatched, committed
    conversation_stage = Column(String, default="ice_breaker") # ice_breaker, building_rapport, escalation, planning
    interest_level = Column(Float, default=1.0) # 0.0 to 1.0. Drops over bad msgs.
    messages_count = Column(Integer, default=0) # Track how many messages sent total
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    messages = relationship("Message", back_populates="match", cascade="all, delete-orphan")

class Like(Base):
    __tablename__ = "likes"

    id = Column(String, primary_key=True, default=generate_uuid)
    sender_id = Column(String, ForeignKey("agents.id"))
    receiver_id = Column(String, ForeignKey("agents.id"))
    status = Column(String, default="pending") # pending, accepted, rejected
    reason = Column(Text, nullable=True) # E.g., "Love your energy!"
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id"))
    memory_type = Column(String, nullable=False) # preference, dislike, pattern, success
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5) # 0.0 to 1.0
    created_from_match = Column(String, ForeignKey("matches.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    match_id = Column(String, ForeignKey("matches.id"))
    sender_agent_id = Column(String, ForeignKey("agents.id"))
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    match = relationship("Match", back_populates="messages")
