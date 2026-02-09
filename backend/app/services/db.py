from supabase import Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client directly
supabase = Client(
    supabase_url=settings.supabase_url,
    supabase_key=settings.supabase_service_role_key
)


async def init_db():
    """Initialize database connection and verify schema."""
    try:
        # Test connection
        response = supabase.table("conversations").select("count").execute()
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def create_conversation(user_id: str, title: str) -> dict:
    """Create a new conversation."""
    try:
        response = supabase.table("conversations").insert({
            "user_id": user_id,
            "title": title
        }).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise


async def get_conversations(user_id: str) -> list:
    """Get all conversations for a user."""
    try:
        response = supabase.table("conversations").select(
            "*"
        ).eq("user_id", user_id).order("updated_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to get conversations: {str(e)}")
        raise


async def get_conversation(conversation_id: str, user_id: str) -> dict:
    """Get a specific conversation."""
    try:
        response = supabase.table("conversations").select(
            "*"
        ).eq("id", conversation_id).eq("user_id", user_id).single().execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to get conversation: {str(e)}")
        raise


async def update_conversation_title(conversation_id: str, title: str) -> dict:
    """Update conversation title."""
    try:
        response = supabase.table("conversations").update({
            "title": title
        }).eq("id", conversation_id).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to update conversation: {str(e)}")
        raise


async def create_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    tool_calls: list = None,
    metadata: dict = None
) -> dict:
    """Create a new message."""
    try:
        message_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content
        }
        
        if tool_calls:
            message_data["tool_calls"] = tool_calls
            
        if metadata:
            message_data["metadata"] = metadata
            
        response = supabase.table("messages").insert(message_data).execute()
        
        # Update conversation timestamp
        supabase.table("conversations").update({
            "updated_at": "now()"
        }).eq("id", conversation_id).execute()
        
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to create message: {str(e)}")
        raise


async def get_messages(conversation_id: str, user_id: str) -> list:
    """Get all messages for a conversation."""
    try:
        response = supabase.table("messages").select(
            "*"
        ).eq("conversation_id", conversation_id).eq("user_id", user_id).order("timestamp", asc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to get messages: {str(e)}")
        raise


async def delete_conversation(conversation_id: str, user_id: str) -> bool:
    """Delete a conversation and its messages."""
    try:
        # Delete messages first (due to foreign key constraint)
        supabase.table("messages").delete().eq("conversation_id", conversation_id).execute()
        
        # Delete conversation
        supabase.table("conversations").delete().eq("id", conversation_id).eq("user_id", user_id).execute()
        
        return True
    except Exception as e:
        logger.error(f"Failed to delete conversation: {str(e)}")
        raise
