import logging
from typing import Dict, List, Optional
import uuid
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

# Data file path
DB_FILE = "/app/data/mock_db.json"

# In-memory storage for testing
conversations_db: Dict[str, dict] = {}
messages_db: Dict[str, dict] = {}

def load_db():
    global conversations_db, messages_db
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                conversations_db = data.get("conversations", {})
                messages_db = data.get("messages", {})
                logger.info(f"Loaded {len(conversations_db)} conversations from {DB_FILE}")
    except Exception as e:
        logger.error(f"Failed to load mock DB: {str(e)}")

def save_db():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        with open(DB_FILE, 'w') as f:
            json.dump({
                "conversations": conversations_db,
                "messages": messages_db
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save mock DB: {str(e)}")

async def init_db():
    """Initialize database connection and verify schema."""
    load_db()
    logger.info("Mock database initialized successfully")

async def create_conversation(user_id: str, title: str) -> dict:
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = {
        "id": conversation_id,
        "user_id": user_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    conversations_db[conversation_id] = conversation
    save_db()
    logger.info(f"Created conversation: {conversation_id}")
    return conversation

async def get_user_conversations(user_id: str) -> List[dict]:
    """Get all conversations for a user."""
    user_conversations = [
        conv for conv in conversations_db.values() 
        if str(conv.get("user_id")) == str(user_id)
    ]
    return sorted(user_conversations, key=lambda x: x.get("updated_at", ""), reverse=True)

async def get_conversation(conversation_id: str, user_id: str) -> Optional[dict]:
    """Get a specific conversation."""
    conversation = conversations_db.get(conversation_id)
    if conversation and str(conversation.get("user_id")) == str(user_id):
        return conversation
    return None

async def create_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    tool_calls: list = None,
    metadata: dict = None
) -> dict:
    """Create a new message."""
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "tool_calls": tool_calls or [],
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    messages_db[message_id] = message
    
    # Update conversation timestamp
    if conversation_id in conversations_db:
        conversations_db[conversation_id]["updated_at"] = datetime.utcnow().isoformat()
    
    save_db()
    logger.info(f"Created message: {message_id}")
    return message

async def get_conversation_messages(conversation_id: str, user_id: str) -> List[dict]:
    """Get all messages for a conversation."""
    conversation_messages = [
        msg for msg in messages_db.values() 
        if msg.get("conversation_id") == conversation_id and str(msg.get("user_id")) == str(user_id)
    ]
    return sorted(conversation_messages, key=lambda x: x.get("timestamp", ""))

async def delete_conversation(conversation_id: str, user_id: str) -> bool:
    """Delete a conversation and its messages."""
    conversation = conversations_db.get(conversation_id)
    if conversation and str(conversation.get("user_id")) == str(user_id):
        # Delete messages
        messages_to_delete = [
            msg_id for msg_id, msg in messages_db.items()
            if msg.get("conversation_id") == conversation_id
        ]
        for msg_id in messages_to_delete:
            del messages_db[msg_id]
        
        # Delete conversation
        del conversations_db[conversation_id]
        save_db()
        return True
    return False
