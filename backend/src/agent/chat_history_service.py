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
        print(f"[DEBUG] Creating new conversation with title: '{title}', user_id: {user_id}")
        conversation = Conversation(
            title=title,
            user_id=user_id,
            extra_data=extra_data or {}
        )
        self.db.add(conversation)
        print(f"[DEBUG] Added conversation to session, committing to database...")
        self.db.commit()
        self.db.refresh(conversation)
        print(f"[DEBUG] Conversation saved successfully with ID: {conversation.id}")
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
        print(f"[DEBUG] Adding message to conversation {conversation_id}: type='{message_type}', content_length={len(content)}")
        
        # Get current message count for sequence numbering
        message_count = self.db.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation_id
        ).scalar()
        
        print(f"[DEBUG] Current message count for conversation: {message_count}")
        
        message = Message(
            conversation_id=conversation_id,
            type=message_type,
            content=content,
            extra_data=extra_data or {},
            sequence_number=message_count + 1
        )
        
        self.db.add(message)
        print(f"[DEBUG] Message added to session with sequence number: {message_count + 1}")
        
        # Update conversation message count and last activity
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            print(f"[DEBUG] Updating conversation metadata: old_count={conversation.message_count}, new_count={message_count + 1}")
            conversation.message_count = message_count + 1
            conversation.updated_at = datetime.utcnow()
            
            # Auto-generate title from first human message if still default
            if conversation.title == "New Conversation" and message_type == "human":
                new_title = self._generate_conversation_title(content)
                print(f"[DEBUG] Auto-generating conversation title: '{new_title}'")
                conversation.title = new_title
        else:
            print(f"[DEBUG] WARNING: Conversation {conversation_id} not found!")
        
        print(f"[DEBUG] Committing message and conversation updates to database...")
        self.db.commit()
        self.db.refresh(message)
        print(f"[DEBUG] Message saved successfully with ID: {message.id}")
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
        print(f"[DEBUG] Adding {len(events)} processing events to message {message_id}")
        processing_events = []
        
        for i, event_data in enumerate(events):
            event_type = event_data.get('event_type', 'unknown')
            title = event_data.get('title', '')
            print(f"[DEBUG] Processing event {i+1}/{len(events)}: type='{event_type}', title='{title}'")
            
            event = ProcessingEvent(
                message_id=message_id,
                event_type=event_type,
                title=title,
                data=event_data.get('data', '')
            )
            self.db.add(event)
            processing_events.append(event)
        
        print(f"[DEBUG] Committing {len(processing_events)} processing events to database...")
        self.db.commit()
        print(f"[DEBUG] Processing events saved successfully")
        return processing_events
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str
    ) -> Optional[Conversation]:
        """Update conversation title"""
        print(f"[DEBUG] Updating conversation {conversation_id} title to: '{title}'")
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            old_title = conversation.title
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            print(f"[DEBUG] Title changed from '{old_title}' to '{title}', committing to database...")
            self.db.commit()
            self.db.refresh(conversation)
            print(f"[DEBUG] Conversation title updated successfully")
        else:
            print(f"[DEBUG] WARNING: Conversation {conversation_id} not found for title update!")
        
        return conversation
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Soft delete a conversation"""
        print(f"[DEBUG] Soft deleting conversation {conversation_id}")
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            old_status = conversation.status
            conversation.status = 'deleted'
            conversation.updated_at = datetime.utcnow()
            print(f"[DEBUG] Conversation status changed from '{old_status}' to 'deleted', committing to database...")
            self.db.commit()
            print(f"[DEBUG] Conversation deleted successfully")
            return True
        else:
            print(f"[DEBUG] WARNING: Conversation {conversation_id} not found for deletion!")
        
        return False
    
    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation"""
        print(f"[DEBUG] Archiving conversation {conversation_id}")
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            old_status = conversation.status
            conversation.status = 'archived'
            conversation.updated_at = datetime.utcnow()
            print(f"[DEBUG] Conversation status changed from '{old_status}' to 'archived', committing to database...")
            self.db.commit()
            print(f"[DEBUG] Conversation archived successfully")
            return True
        else:
            print(f"[DEBUG] WARNING: Conversation {conversation_id} not found for archiving!")
        
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
        print(f"[DEBUG] Cleaning up sessions older than {hours} hours")
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        print(f"[DEBUG] Cutoff time: {cutoff_time}")
        
        count = self.db.query(SessionModel).filter(
            SessionModel.last_activity < cutoff_time,
            SessionModel.status == 'active'
        ).update({"status": "expired"})
        
        print(f"[DEBUG] Expiring {count} old sessions, committing to database...")
        self.db.commit()
        print(f"[DEBUG] Session cleanup completed, {count} sessions expired")
        return count

    async def manual_save_conversation(self, conversation_id: str) -> Conversation:
        """Manually save/refresh a conversation to ensure persistence"""
        print(f"[DEBUG] Manual save requested for conversation {conversation_id}")
        
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Update the updated_at timestamp to indicate manual save
        old_time = conversation.updated_at
        conversation.updated_at = datetime.utcnow()
        print(f"[DEBUG] Updated conversation timestamp from {old_time} to {conversation.updated_at}")
        
        # Commit the changes
        print(f"[DEBUG] Committing manual save to database...")
        self.db.commit()
        self.db.refresh(conversation)
        print(f"[DEBUG] Conversation manually saved successfully")
        
        return conversation
