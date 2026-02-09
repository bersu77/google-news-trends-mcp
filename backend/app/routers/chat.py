from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import StreamingResponse
import json
import logging
import uuid
from typing import Dict, Any

from app.core.config import settings
from app.schemas.chat import ChatRequest, StreamingChunk
from app.services.db import create_conversation, get_conversation, create_message, get_user_conversations, get_conversation_messages
from app.services.agent.react_agent import get_chat_agent as get_real_agent
from app.services.mock_agent import get_chat_agent as get_mock_agent

def get_chat_agent():
    if settings.use_mock_agent:
        return get_mock_agent()
    return get_real_agent()

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/stream")
async def chat_stream(request: ChatRequest, http_request: Request):
    try:
        user_id = http_request.state.user_id
        conversation_id = request.conversation_id
        
        if not conversation_id:
            conversation = await create_conversation(
                user_id=user_id,
                title=request.message[:50] + ("..." if len(request.message) > 50 else "")
            )
            conversation_id = conversation["id"]
        else:
            conversation = await get_conversation(conversation_id, user_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        
        user_message_id = str(uuid.uuid4())
        await create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=request.message
        )
        
        logger.info(f"Using agent from: {get_chat_agent.__module__}")
        agent = get_chat_agent()
        
        async def generate_response():
            assistant_content = ""
            tool_calls = []
            
            try:
                async for chunk in agent.chat_stream(request.message, conversation_id, user_id):
                    chunk_data = {
                        "id": str(uuid.uuid4()),
                        "event": "message",
                        "data": json.dumps(chunk.dict() if hasattr(chunk, 'dict') else chunk)
                    }
                    
                    yield f"id: {chunk_data['id']}\nevent: {chunk_data['event']}\ndata: {chunk_data['data']}\n\n"
                    
                    if chunk.get("type") == "content":
                        assistant_content = chunk.get("content", "")
                        tool_calls = chunk.get("tool_calls", [])
                    
                    elif chunk.get("type") == "token":
                        assistant_content += chunk.get("token", "")
                    
                    elif chunk.get("type") == "error":
                        assistant_content = chunk.get("content", "An error occurred")
                
                yield f"id: {str(uuid.uuid4())}\nevent: done\ndata: {json.dumps({'conversation_id': conversation_id})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                error_chunk = {
                    "type": "error",
                    "content": "I apologize, but I encountered an error while processing your request.",
                    "conversation_id": conversation_id
                }
                yield f"id: {str(uuid.uuid4())}\nevent: error\ndata: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except HTTPException as e:
        # Re-raise HTTP exceptions so they return the correct status code
        raise e
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/conversations")
async def create_new_conversation(request: Request):
    try:
        user_id = request.state.user_id
        body = await request.json()
        title = body.get("title", "New Conversation")
        
        conversation = await create_conversation(
            user_id=user_id,
            title=title
        )
        return conversation
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.get("/conversations")
async def get_conversations_list(request: Request):
    try:
        user_id = request.state.user_id
        conversations = await get_user_conversations(user_id)
        return {"conversations": conversations}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, request: Request):
    try:
        user_id = request.state.user_id
        messages = await get_conversation_messages(conversation_id, user_id)
        return {"messages": messages}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )
