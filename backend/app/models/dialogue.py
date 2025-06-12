from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class DialogueSession(Base):
    __tablename__ = "dialogue_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    status = Column(String, default="active")  # active, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("DialogueMessage", back_populates="session")
    context = relationship("DialogueContext", back_populates="session", uselist=False)


class DialogueMessage(Base):
    __tablename__ = "dialogue_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("dialogue_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("DialogueSession", back_populates="messages")


class DialogueContext(Base):
    __tablename__ = "dialogue_contexts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("dialogue_sessions.id"), nullable=False)
    extracted_info = Column(JSON, default=dict)
    completeness_score = Column(Integer, default=0)
    current_phase = Column(String, default="gathering")  # gathering, clarifying, planning
    last_question_type = Column(String, nullable=True)
    
    # Relationships
    session = relationship("DialogueSession", back_populates="context")