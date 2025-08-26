"""
Chat History Models and Database Schema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    user_id = Column(String(100), nullable=True)  # For future user management
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default='active')  # active, archived, deleted
    extra_data = Column(JSON, nullable=True)  # Additional conversation data
    summary = Column(Text, nullable=True)  # AI-generated summary
    message_count = Column(Integer, default=0)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    type = Column(String(20), nullable=False)  # 'human', 'ai', 'system'
    content = Column(Text, nullable=False)
    extra_data = Column(JSON, nullable=True)  # Sources, citations, processing events
    created_at = Column(DateTime, default=datetime.utcnow)
    sequence_number = Column(Integer, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    processing_events = relationship("ProcessingEvent", back_populates="message", cascade="all, delete-orphan")

class ProcessingEvent(Base):
    __tablename__ = "processing_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'generate_query', 'web_research', etc.
    title = Column(String(255), nullable=False)
    data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="processing_events")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='active')  # active, expired
    
    # Relationships
    conversation = relationship("Conversation", back_populates="sessions")
