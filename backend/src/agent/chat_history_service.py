"""
Chat History Service - Business Logic for Conversation Management
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from agent.models import Conversation, Message, ProcessingEvent, Session as SessionModel
from agent.database import get_db
import uuid

class ChatHistoryService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_conversation(
        self, 
        title: str = "New Conversation",
        user_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            title=title,
            user_id=user_id,
            extra_data=extra_data or {}
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.status == 'active'
        ).first()
    
    async def get_conversations(
        self, 
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None
    ) -> List[Conversation]:
        """Get conversations with optional filtering"""
        query = self.db.query(Conversation).filter(
            Conversation.status == 'active'
        )
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        if search_query:
            query = query.filter(
                or_(
                    Conversation.title.ilike(f"%{search_query}%"),
                    Conversation.summary.ilike(f"%{search_query}%")
                )
            )
        
        return query.order_by(desc(Conversation.updated_at)).offset(offset).limit(limit).all()
    
    async def add_message(
        self,
        conversation_id: str,
        message_type: str,  # 'human', 'ai', 'system'
        content: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to a conversation"""
        # Get current message count for sequence numbering
        message_count = self.db.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation_id
        ).scalar()
        
        message = Message(
            conversation_id=conversation_id,
            type=message_type,
            content=content,
            extra_data=extra_data or {},
            sequence_number=message_count + 1
        )
        
        self.db.add(message)
        
        # Update conversation message count and last activity
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.message_count = message_count + 1
            conversation.updated_at = datetime.utcnow()
            
            # Auto-generate title from first human message if still default
            if conversation.title == "New Conversation" and message_type == "human":
                conversation.title = self._generate_conversation_title(content)
        
        self.db.commit()
        self.db.refresh(message)
        return message
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """Get messages for a conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.sequence_number).offset(offset).limit(limit).all()
    
    async def add_processing_events(
        self,
        message_id: str,
        events: List[Dict[str, Any]]
    ) -> List[ProcessingEvent]:
        """Add processing events to a message"""
        processing_events = []
        
        for event_data in events:
            event = ProcessingEvent(
                message_id=message_id,
                event_type=event_data.get('event_type', 'unknown'),
                title=event_data.get('title', ''),
                data=event_data.get('data', '')
            )
            self.db.add(event)
            processing_events.append(event)
        
        self.db.commit()
        return processing_events
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str
    ) -> Optional[Conversation]:
        """Update conversation title"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(conversation)
        
        return conversation
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Soft delete a conversation"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.status = 'deleted'
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.status = 'archived'
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    async def generate_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """Generate AI summary of conversation (placeholder for future implementation)"""
        # This would use your LLM to summarize the conversation
        # For now, return a simple summary based on message count
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            return f"Conversation with {conversation.message_count} messages"
        return None
    
    async def search_conversations(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by content"""
        # This could be enhanced with full-text search
        base_query = self.db.query(Conversation).filter(
            Conversation.status == 'active'
        )
        
        if user_id:
            base_query = base_query.filter(Conversation.user_id == user_id)
        
        # Search in conversation titles and message content
        conversation_ids = self.db.query(Message.conversation_id).filter(
            Message.content.ilike(f"%{query}%")
        ).distinct()
        
        return base_query.filter(
            or_(
                Conversation.title.ilike(f"%{query}%"),
                Conversation.id.in_(conversation_ids)
            )
        ).order_by(desc(Conversation.updated_at)).limit(limit).all()
    
    async def get_conversation_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get conversation statistics"""
        base_query = self.db.query(Conversation)
        
        if user_id:
            base_query = base_query.filter(Conversation.user_id == user_id)
        
        total_conversations = base_query.filter(
            Conversation.status == 'active'
        ).count()
        
        archived_conversations = base_query.filter(
            Conversation.status == 'archived'
        ).count()
        
        total_messages = self.db.query(Message).join(Conversation).filter(
            Conversation.user_id == user_id if user_id else True,
            Conversation.status == 'active'
        ).count()
        
        return {
            "total_conversations": total_conversations,
            "archived_conversations": archived_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": total_messages / max(total_conversations, 1)
        }
    
    def _generate_conversation_title(self, first_message: str) -> str:
        """Generate a conversation title from the first message"""
        # Simple title generation - could be enhanced with AI
        words = first_message.strip().split()
        if len(words) <= 6:
            return first_message.strip()
        else:
            return " ".join(words[:6]) + "..."
    
    async def cleanup_old_sessions(self, hours: int = 24) -> int:
        """Clean up old inactive sessions"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        count = self.db.query(SessionModel).filter(
            SessionModel.last_activity < cutoff_time,
            SessionModel.status == 'active'
        ).update({"status": "expired"})
        
        self.db.commit()
        return count
