from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Float
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
    insights = relationship("ConversationInsight", back_populates="session")


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
    key_topics = Column(JSON, default=list)  # 主要トピックのリスト
    message_count = Column(Integer, default=0)
    
    # Relationships
    session = relationship("DialogueSession", back_populates="context")


class ConversationInsight(Base):
    """過去の会話から抽出された洞察"""
    __tablename__ = "conversation_insights"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("dialogue_sessions.id"), nullable=False)
    user_id = Column(String, nullable=False)
    insight_type = Column(String, nullable=False)  # challenge, preference, strength, weakness
    content = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)  # 0.0-1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # メタデータ（どの会話から抽出されたか等）
    insight_metadata = Column(JSON, default=dict)
    
    # Relationships
    session = relationship("DialogueSession", back_populates="insights")


class UserProfile(Base):
    """ユーザープロファイル（複数セッションから集約された情報）"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, nullable=False)
    
    # 集約された情報
    common_challenges = Column(JSON, default=list)  # よくある課題
    strengths = Column(JSON, default=list)  # 強み
    improvement_areas = Column(JSON, default=list)  # 改善領域
    preferred_learning_style = Column(String, nullable=True)  # 学習スタイル
    
    # 統計情報
    total_sessions = Column(Integer, default=0)
    completed_actions = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationPattern(Base):
    """ユーザーの会話パターン"""
    __tablename__ = "conversation_patterns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    pattern_type = Column(String, nullable=False)  # response_style, topic_preference, etc.
    pattern_data = Column(JSON, default=dict)
    frequency = Column(Integer, default=1)
    last_observed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)