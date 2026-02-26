from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Float
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
    creator_id = Column(String, index=True, nullable=True) # ID of the user who made it (optional for MVP)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent1_id = Column(String, ForeignKey("agents.id"))
    agent2_id = Column(String, ForeignKey("agents.id"))
    compatibility_score = Column(Float, default=0.0) # Cosine similarity from Pinecone
    status = Column(String, default="active") # active, ghosted, committed
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    messages = relationship("Message", back_populates="match", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    match_id = Column(String, ForeignKey("matches.id"))
    sender_agent_id = Column(String, ForeignKey("agents.id"))
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    match = relationship("Match", back_populates="messages")
