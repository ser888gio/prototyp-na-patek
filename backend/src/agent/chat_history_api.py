"""
Enhanced Chat History API Endpoints
Add these to your existing app.py file
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator
from datetime import datetime
from agent.database import get_db
from agent.chat_history_service import ChatHistoryService
from agent.models import Conversation, Message
import uuid

# Create router for chat history endpoints
chat_history_router = APIRouter(prefix="/api/chat-history", tags=["chat-history"])

# Pydantic models for request/response
class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    user_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    status: str
    message_count: int
    summary: Optional[str] = None
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    type: str  # 'human', 'ai', 'system'
    content: str
    extra_data: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    type: str
    content: str
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime
    sequence_number: int
    
    @field_validator('id', 'conversation_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True
    
    class Config:
        from_attributes = True

class ProcessingEventCreate(BaseModel):
    event_type: str
    title: str
    data: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None

# Endpoints
@chat_history_router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    service = ChatHistoryService(db)
    new_conversation = await service.create_conversation(
        title=conversation.title,
        user_id=conversation.user_id,
        extra_data=conversation.extra_data
    )
    return new_conversation

@chat_history_router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get conversations with optional filtering"""
    service = ChatHistoryService(db)
    conversations = await service.get_conversations(
        user_id=user_id,
        limit=limit,
        offset=offset,
        search_query=search
    )
    return conversations

@chat_history_router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific conversation"""
    service = ChatHistoryService(db)
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@chat_history_router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """Update conversation details"""
    service = ChatHistoryService(db)
    
    if conversation_update.title:
        updated_conversation = await service.update_conversation_title(
            conversation_id, conversation_update.title
        )
        if not updated_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return updated_conversation
    
    # If no updates, just return current conversation
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@chat_history_router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    archive_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Delete or archive a conversation"""
    service = ChatHistoryService(db)
    
    if archive_only:
        success = await service.archive_conversation(conversation_id)
        action = "archived"
    else:
        success = await service.delete_conversation(conversation_id)
        action = "deleted"
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": f"Conversation {action} successfully"}

@chat_history_router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """Add a message to a conversation"""
    service = ChatHistoryService(db)
    
    # Verify conversation exists
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    new_message = await service.add_message(
        conversation_id=conversation_id,
        message_type=message.type,
        content=message.content,
        extra_data=message.extra_data
    )
    return new_message

@chat_history_router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(100, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get messages for a conversation"""
    service = ChatHistoryService(db)
    
    # Verify conversation exists
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await service.get_messages(
        conversation_id=conversation_id,
        limit=limit,
        offset=offset
    )
    return messages

@chat_history_router.post("/messages/{message_id}/processing-events")
async def add_processing_events(
    message_id: str,
    events: List[ProcessingEventCreate],
    db: Session = Depends(get_db)
):
    """Add processing events to a message"""
    service = ChatHistoryService(db)
    
    events_data = [
        {
            "event_type": event.event_type,
            "title": event.title,
            "data": event.data
        }
        for event in events
    ]
    
    processing_events = await service.add_processing_events(message_id, events_data)
    return {"message": f"Added {len(processing_events)} processing events"}

@chat_history_router.get("/search")
async def search_conversations(
    query: str = Query(..., min_length=1),
    user_id: Optional[str] = Query(None),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db)
):
    """Search conversations by content"""
    service = ChatHistoryService(db)
    results = await service.search_conversations(
        query=query,
        user_id=user_id,
        limit=limit
    )
    return results

@chat_history_router.get("/stats")
async def get_conversation_stats(
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get conversation statistics"""
    service = ChatHistoryService(db)
    stats = await service.get_conversation_stats(user_id=user_id)
    return stats

@chat_history_router.post("/cleanup-sessions")
async def cleanup_old_sessions(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    db: Session = Depends(get_db)
):
    """Cleanup old inactive sessions"""
    service = ChatHistoryService(db)
    cleaned_count = await service.cleanup_old_sessions(hours=hours)
    return {"message": f"Cleaned up {cleaned_count} old sessions"}

# Export the router to be included in your main app
__all__ = ["chat_history_router"]
