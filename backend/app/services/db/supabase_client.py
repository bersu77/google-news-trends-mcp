from supabase import create_client, Client
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)


async def create_conversation(user_id: str, title: str) -> Dict[str, Any]:
    try:
        response = supabase.table("conversations").insert({
            "user_id": user_id,
            "title": title
        }).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise Exception("Failed to create conversation")
            
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise


async def get_conversation(conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = supabase.table("conversations").select("*").eq("id", conversation_id).eq("user_id", user_id).execute()
        
        if response.data:
            return response.data[0]
        return None
        
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise


async def get_user_conversations(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    try:
        response = supabase.table("conversations").select("*").eq("user_id", user_id).order("updated_at", desc=True).limit(limit).execute()
        
        return response.data or []
        
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise


async def create_message(conversation_id: str, user_id: str, role: str, content: str, 
                        tool_calls: Optional[List[Dict[str, Any]]] = None, 
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        message_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if tool_calls:
            message_data["tool_calls"] = tool_calls
            
        if metadata:
            message_data["metadata"] = metadata
            
        response = supabase.table("messages").insert(message_data).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise Exception("Failed to create message")
            
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise


async def get_conversation_messages(conversation_id: str, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    try:
        response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).eq("user_id", user_id).order("timestamp", desc=False).limit(limit).execute()
        
        return response.data or []
        
    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}")
        raise


async def update_conversation_timestamp(conversation_id: str) -> None:
    try:
        supabase.table("conversations").update({
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", conversation_id).execute()
        
    except Exception as e:
        logger.error(f"Error updating conversation timestamp: {str(e)}")


async def init_db():
    try:
        response = supabase.table("conversations").select("id").limit(1).execute()
        logger.info("Database connection successful")
    except Exception as e:
        error_msg = str(e)
        if "PGRST205" in error_msg or "conversations" in error_msg.lower():
            logger.error(f"Database initialization failed: Tables missing. Please run the contents of 'supabase_schema.sql' in your Supabase SQL Editor. Error: {error_msg}")
        else:
            logger.error(f"Database initialization failed: {error_msg}")
        raise
