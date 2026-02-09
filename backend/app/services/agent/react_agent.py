from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import AsyncCallbackHandler
import logging
import uuid
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
import asyncio
from asgiref.sync import async_to_sync

class ActivityCallbackHandler(AsyncCallbackHandler):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        await self.queue.put({"type": "token", "token": token})

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        name = serialized.get("name")
        label = f"Using tool: {name}..."
        if name == "web_search": label = "Searching the web..."
        elif name == "google_news_search": label = "Searching Google News..."
        elif name == "google_trends": label = "Analyzing trends..."
        await self.queue.put({"type": "activity", "content": label})

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        await self.queue.put({"type": "activity", "content": "Summarizing results..."})

from app.core.config import settings
from app.services.tools import get_tavily_tool, get_google_trends_tool
from app.services.db import get_conversation_messages, create_message
from app.schemas.chat import MessageRole, ToolCall

logger = logging.getLogger(__name__)


class ChatAgent:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.activity_handler = ActivityCallbackHandler(self.queue)
        self.llm = ChatOpenAI(
            model_name=settings.model_name,
            temperature=0,
            openai_api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            streaming=True,
            callbacks=[self.activity_handler]
        )
        
        self.tavily_tool = get_tavily_tool()
        self.google_trends_tool = get_google_trends_tool()
        
        self.tools = [
            Tool(
                name="web_search",
                description="Search the web for current information using Tavily. Use this for questions about recent events, news, or general web queries.",
                func=self._tavily_search
            ),
            Tool(
                name="google_news_search",
                description="Search Google News for recent news articles. Use this for questions about current news and events.",
                func=self._google_news_search
            ),
            Tool(
                name="google_trends",
                description="Get Google Trends data for specific keywords. Use this to analyze search trends and popularity over time.",
                func=self._google_trends
            )
        ]
        
        self.prompt = PromptTemplate.from_template("""
You are a helpful AI assistant with access to web search, Google News, and Google Trends tools. 
You can provide current information and analyze trends.

Available tools:
{tools}

Tool names: {tool_names}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, MUST be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: If you can answer the question directly without using any tools, you should skip the 'Action:' and 'Action Input:' lines and go straight to 'Final Answer:'.
NEVER use 'None' or any other value not in [{tool_names}] for the 'Action:' field.
You MUST follow the format strictly. Do not include any text before 'Thought:' or after 'Final Answer:'.

Previous conversation:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}

NOTE: If a tool returns an error message (e.g. "Google Trends analysis failed"), you should explain this to the user politely. Do not crash or return raw error codes. If possibly, try an alternative tool or answer based on your knowledge if appropriate.
""")
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            return_messages=True
        )
        
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            memory=self.memory,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    

    def _tavily_search(self, query: str) -> str:
        try:
            result = self.tavily_tool.search(query, max_results=5)
            if result["success"]:
                return f"Search results for '{query}':\n{result['answer']}\n\nSources: {', '.join(result['sources'])}"
            else:
                return f"Search failed: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return "I encountered an error while searching the web."
    
    def _google_news_search(self, query: str) -> str:
        try:
            # Use async_to_sync to run the async tool method in this sync wrapper
            result = async_to_sync(self.google_trends_tool.search_google_news)(query)
            
            if result["success"]:
                return f"Google News results for '{query}':\n{result['data']}"
            else:
                return f"Google News search failed: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Google News search error: {str(e)}")
            return "I encountered an error while searching Google News."
    
    def _google_trends(self, keywords: str) -> str:
        try:
            keyword_list = [k.strip() for k in keywords.split(",")]
            # Use async_to_sync to run the async tool method
            result = async_to_sync(self.google_trends_tool.get_google_trends)(keyword_list)
            
            if result["success"]:
                return f"Google Trends data for '{keywords}':\n{result['data']}"
            else:
                return f"Google Trends analysis failed: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Google Trends error: {str(e)}")
            return "I encountered an error while analyzing Google Trends."
    
    async def load_conversation_history(self, conversation_id: str, user_id: str):
        try:
            messages = await get_conversation_messages(conversation_id, user_id)
            
            self.memory.clear()
            
            for msg in messages:
                if msg["role"] == MessageRole.USER:
                    self.memory.chat_memory.add_user_message(msg["content"])
                elif msg["role"] == MessageRole.ASSISTANT:
                    self.memory.chat_memory.add_ai_message(msg["content"])
                    
        except Exception as e:
            logger.error(f"Error loading conversation history: {str(e)}")
    
    async def chat_stream(self, message: str, conversation_id: str, user_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info(f"ChatAgent.chat_stream called for conversation: {conversation_id}")
        message_id = str(uuid.uuid4())
        
        try:
            await self.load_conversation_history(conversation_id, user_id)
            
            tool_calls = []
            
            async def process_agent_response():
                try:
                    # Run agent in a separate task
                    agent_task = asyncio.create_task(self.agent_executor.ainvoke(
                        {"input": message},
                        config={"callbacks": [self.activity_handler], "run_name": "AssistantStream"}
                    ))
                    
                    full_content = ""
                    final_answer_started = False
                    
                    # Consume chunks from the queue
                    while True:
                        try:
                            # Use a small timeout to check if the agent task is done
                            chunk = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                            
                            if chunk["type"] == "activity":
                                yield {
                                    "type": "activity",
                                    "content": chunk["content"],
                                    "conversation_id": conversation_id,
                                    "message_id": message_id
                                }
                            
                            elif chunk["type"] == "token":
                                token = chunk["token"]
                                if "Final Answer:" in token:
                                    final_answer_started = True
                                    parts = token.split("Final Answer:", 1)
                                    if len(parts) > 1:
                                        token = parts[1]
                                    # Clear activity when actual answer starts
                                    yield {
                                        "type": "activity",
                                        "content": "",
                                        "conversation_id": conversation_id,
                                        "message_id": message_id
                                    }
                                
                                if final_answer_started:
                                    if not token.strip() and not full_content:
                                        continue
                                    full_content += token
                                    yield {
                                        "type": "token",
                                        "token": token,
                                        "conversation_id": conversation_id,
                                        "message_id": message_id
                                    }
                        except asyncio.TimeoutError:
                            if agent_task.done():
                                break
                            continue
                    
                    response = await agent_task
                    
                    intermediate_steps = response.get("intermediate_steps", [])
                    for step in intermediate_steps:
                        if len(step) >= 2:
                            action, observation = step[0], step[1]
                            if action.tool == "_Exception":
                                continue
                            
                            t_call = ToolCall(
                                id=str(uuid.uuid4()),
                                name=action.tool,
                                arguments=action.tool_input,
                                result=str(observation),
                                status="completed"
                            )
                            tool_calls.append(t_call)
                    
                    final_answer = response.get("output", full_content or "I processed your request.")
                    
                    # Save assistant message to DB
                    await create_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="assistant",
                        content=final_answer,
                        tool_calls=[tc.dict() for tc in tool_calls]
                    )
                    
                    yield {
                        "type": "content",
                        "content": final_answer,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                        "tool_calls": [tc.dict() for tc in tool_calls]
                    }
                    
                except Exception as e:
                    logger.error(f"Agent execution error: {str(e)}")
                    yield {
                        "type": "error",
                        "content": "I apologize, but I encountered an error while processing your request.",
                        "conversation_id": conversation_id,
                        "message_id": message_id
                    }
            
            async for chunk in process_agent_response():
                yield chunk
                
        except Exception as e:
            logger.error(f"Chat stream error: {str(e)}")
            yield {
                "type": "error",
                "content": "I apologize, but I encountered an error while processing your request.",
                "conversation_id": conversation_id,
                "message_id": message_id
            }


def get_chat_agent() -> ChatAgent:
    return ChatAgent()
