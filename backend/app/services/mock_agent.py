# Mock agent service for testing without complex dependencies
import logging
import uuid
from typing import Dict, Any, AsyncGenerator

logger = logging.getLogger(__name__)


class MockChatAgent:
    def __init__(self):
        pass
    
    async def chat_stream(self, message: str, conversation_id: str, user_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        message_id = str(uuid.uuid4())
        
        try:
            # Simulate tool call for web search
            yield {
                "type": "tool_call",
                "tool_call": {
                    "id": str(uuid.uuid4()),
                    "name": "web_search",
                    "arguments": message,
                    "result": f"Mock search results for '{message}': This is a simulated response since the backend dependencies are not fully installed.",
                    "status": "completed"
                },
                "conversation_id": conversation_id,
                "message_id": message_id
            }
            
            # Simulate final response
            yield {
                "type": "content",
                "content": f"Hello! I received your message: '{message}'. This is a mock response because the full agent dependencies (langchain, openai, etc.) are not installed. The conversation ID is {conversation_id}. In a production environment, I would use web search and AI tools to provide a proper response.",
                "conversation_id": conversation_id,
                "message_id": message_id,
                "tool_calls": []
            }
            
        except Exception as e:
            logger.error(f"Mock chat stream error: {str(e)}")
            yield {
                "type": "error",
                "content": "I apologize, but I encountered an error while processing your request.",
                "conversation_id": conversation_id,
                "message_id": message_id
            }


def get_chat_agent() -> MockChatAgent:
    return MockChatAgent()
