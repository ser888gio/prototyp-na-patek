"""
Database initialization and migration script
Run this to set up the chat history database
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy import text
from agent.database import engine, create_tables, get_db
from agent.models import Base

async def initialize_database():
    """Initialize the database with all required tables"""
    print("🔄 Initializing chat history database...")
    
    try:
        # Create all tables
        create_tables()
        print("✅ Database tables created successfully")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                print("✅ Database connection test successful")
        
        print("🎉 Chat history database setup complete!")
        print("\nCreated tables:")
        print("- messages: Store individual messages")
        print("- processing_events: Store AI processing steps")
        print("- sessions: Store user session data")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

async def test_database_operations():
    """Test basic database operations"""
    print("\n🧪 Testing database operations...")
    
    try:
        from agent.chat_history_service import ChatHistoryService
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        service = ChatHistoryService(db)
        
        # Test conversation creation
        conversation = await service.create_conversation(
            title="Test Conversation",
            user_id="test-user"
        )
        print(f"✅ Created test conversation: {conversation.id}")
        
        # Test message creation
        message = await service.add_message(
            conversation_id=str(conversation.id),
            message_type="human",
            content="Hello, this is a test message!"
        )
        print(f"✅ Added test message: {message.id}")
        
        # Test conversation retrieval
        conversations = await service.get_conversations(user_id="test-user")
        print(f"✅ Retrieved {len(conversations)} conversations")
        
        # Test message retrieval
        messages = await service.get_messages(conversation_id=str(conversation.id))
        print(f"✅ Retrieved {len(messages)} messages")
        
        # Cleanup test data
        await service.delete_conversation(str(conversation.id))
        print("✅ Cleaned up test data")
        
        db.close()
        print("🎉 Database operations test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting chat history database setup...")
    
    # Check if required environment variables are set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️  Warning: DATABASE_URL not set, using default PostgreSQL connection")
        print("   Make sure PostgreSQL is running and accessible")
    
    # Run initialization
    success = asyncio.run(initialize_database())
    
    if success:
        # Run tests
        test_success = asyncio.run(test_database_operations())
        
        if test_success:
            print("\n✅ Setup complete! Your chat history system is ready to use.")
            print("\nNext steps:")
            print("1. Add the chat history router to your FastAPI app:")
            print("   from agent.chat_history_api import chat_history_router")
            print("   app.include_router(chat_history_router)")
            print("\n2. Update your frontend to use the new components:")
            print("   - Replace App.tsx with EnhancedApp.tsx")
            print("   - Add ConversationList component")
            print("   - Use useChatHistory hook")
        else:
            print("❌ Setup completed but tests failed. Check your database configuration.")
    else:
        print("❌ Setup failed. Please check your database configuration and try again.")
        print("\nTroubleshooting:")
        print("- Ensure PostgreSQL is running")
        print("- Check DATABASE_URL environment variable")
        print("- Verify database credentials and permissions")
