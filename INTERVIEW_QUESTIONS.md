# Technical Interview Questions - AI Chat System

This document provides detailed explanations for the architectural and implementation decisions in this project.

---

## 1. Why SSE vs WebSocket?

**Choice: Server-Sent Events (SSE)**

### Rationale:
- **Unidirectional streaming**: Our use case is server → client streaming (LLM token generation). SSE is purpose-built for this pattern.
- **Simpler protocol**: SSE uses standard HTTP, no handshake complexity. Works seamlessly with existing infrastructure (load balancers, proxies).
- **Built-in reconnection**: Browsers automatically reconnect on connection drop with `EventSource`.
- **Lower overhead**: No need for bidirectional channel maintenance like WebSocket.
- **Better for LLM streaming**: Token-by-token streaming is inherently one-way. WebSocket's bidirectional capability is unnecessary overhead.

### Implementation:
```python
# backend/app/routers/chat.py
return StreamingResponse(
    generate_response(),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
)
```

**When WebSocket would be better**: Real-time collaborative editing, gaming, or bidirectional chat where client sends frequent updates during streaming.

---

## 2. How ReAct Agent Decides Between Tools

**Decision mechanism: LLM reasoning via prompt engineering**

### Tool Descriptions (from `react_agent.py`):
```python
Tool(
    name="web_search",
    description="Search the web for current information using Tavily. Use this for questions about recent events, news, or general web queries."
)

Tool(
    name="google_trends",
    description="Get Google Trends data for specific keywords. Use this to analyze search trends and popularity over time."
)
```

### How it works:
1. **Prompt template** includes tool descriptions and names
2. **LLM analyzes** the user query semantically
3. **LLM outputs** structured reasoning:
   ```
   Thought: User wants trend analysis for "AI agents"
   Action: google_trends
   Action Input: AI agents
   ```
4. **Agent executor** parses the action and invokes the corresponding tool

### Example decision flow:
- Query: "What is SSE streaming?" → **No tool** (LLM has knowledge)
- Query: "Latest news on AI" → **web_search** (Tavily)
- Query: "Trending searches for Python" → **google_trends** (MCP)

**Key insight**: The LLM's semantic understanding drives tool selection, not hardcoded rules.

---

## 3. How MCP Adapter is Wired

**Architecture: Direct HTTP client to MCP server**

### Connection Flow:
```
Backend (FastAPI) → HTTP POST → MCP Server (FastAPI) → Google Trends API
```

### Implementation (`google_trends_mcp.py`):
```python
async def call_tool(self, tool_name: str, arguments: dict):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments}
    }
    
    # JWT authentication
    headers = {"Authorization": f"Bearer {self.generate_jwt()}"}
    
    # HTTP request to MCP server
    response = await client.post(self.base_url, json=payload, headers=headers)
```

### Key components:
1. **Service discovery**: `GOOGLE_TRENDS_MCP_URL=http://google-trends-mcp:8000/mcp` (Docker service name)
2. **Authentication**: JWT signed with shared secret (`GOOGLE_TRENDS_MCP_JWT_SECRET`)
3. **Protocol**: JSON-RPC 2.0 over HTTP
4. **Error handling**: Retry logic (3 attempts) for transient failures

**Why not use LangChain's MCP adapter?** Direct HTTP gives us:
- Full control over retry logic
- Custom error handling
- Simpler debugging
- No additional dependency complexity

---

## 4. How Supabase RLS Prevents Data Leaks

**Row Level Security (RLS) enforces user isolation at the database level**

### Schema (`supabase_schema.sql`):
```sql
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
```

### Implicit RLS Policies:
When using Supabase client with `service_role_key`, we enforce user isolation in application code:

```python
# backend/app/services/db/supabase_client.py
async def get_user_conversations(user_id: str):
    response = supabase.table("conversations")
        .select("*")
        .eq("user_id", user_id)  # ← User isolation
        .execute()
```

### Protection mechanism:
1. **Middleware extracts** `user_id` from JWT
2. **All DB queries** filter by `user_id`
3. **Even if attacker** modifies request, they can't access other users' data because:
   - JWT signature validation prevents token forgery
   - `user_id` is extracted from verified token, not request body
   - Database queries are scoped to authenticated user

**Defense in depth**: Even if application logic fails, explicit RLS policies (when added) provide a second layer.

---

## 5. How Chat Memory is Loaded into Agent

**Process: Database → LangChain Memory → Agent Context**

### Implementation (`react_agent.py`):
```python
async def load_conversation_history(self, conversation_id: str, user_id: str):
    # 1. Fetch messages from Supabase
    messages = await get_conversation_messages(conversation_id, user_id)
    
    # 2. Clear existing memory
    self.memory.clear()
    
    # 3. Populate LangChain memory
    for msg in messages:
        if msg["role"] == MessageRole.USER:
            self.memory.chat_memory.add_user_message(msg["content"])
        elif msg["role"] == MessageRole.ASSISTANT:
            self.memory.chat_memory.add_ai_message(msg["content"])
```

### Memory injection into agent:
```python
# Called before each agent invocation
await self.load_conversation_history(conversation_id, user_id)

# Memory is passed to agent executor
self.agent_executor = AgentExecutor(
    agent=self.agent,
    memory=self.memory,  # ← ConversationBufferMemory
    ...
)
```

### Prompt template includes memory:
```python
Previous conversation:
{chat_history}  # ← Populated from memory

Question: {input}
```

**Result**: Agent has full context of conversation history for coherent multi-turn dialogue.

---

## 6. How Middleware Blocks Unknown Access

**Authentication flow: JWT validation with JWKS + fallback**

### Middleware (`auth.py`):
```python
class AuthMiddleware:
    async def dispatch(self, request: Request, call_next):
        # 1. Bypass public endpoints
        if request.url.path.startswith("/api/auth/login"):
            return await call_next(request)
        
        # 2. Extract token
        auth_header = request.headers.get("Authorization")
        token = auth_header.replace("Bearer ", "")
        
        # 3. Validate token
        try:
            # Try ES256 (Supabase) via JWKS
            payload = jwt.decode(token, jwks_key, algorithms=["ES256"])
        except:
            # Fallback to HS256 (local tokens)
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        
        # 4. Attach user context
        request.state.user_id = payload.get("sub")
        request.state.email = payload.get("email")
        
        return await call_next(request)
```

### Protection against attacks:
- **No token** → 401 Unauthorized
- **Invalid signature** → JWT decode fails → 401
- **Expired token** → JWT decode fails → 401
- **Tampered payload** → Signature mismatch → 401
- **Unknown algorithm** → Not in allowed list → 401

**Key insight**: Cryptographic signature validation ensures only tokens signed by trusted authority (Supabase or our backend) are accepted.

---

## 7. Docker Networking Decisions

**Architecture: Bridge network with service name resolution**

### Network configuration (`docker-compose.yml`):
```yaml
networks:
  chat-network:
    driver: bridge

services:
  backend:
    networks:
      - chat-network
  
  google-trends-mcp:
    networks:
      - chat-network
```

### Key decisions:

#### 1. **Service name as hostname**
```python
GOOGLE_TRENDS_MCP_URL=http://google-trends-mcp:8000/mcp
#                            ↑ Service name, not localhost
```
**Why**: Docker's embedded DNS resolves service names to container IPs within the same network.

#### 2. **Internal vs external ports**
```yaml
google-trends-mcp:
  ports:
    - "8001:8000"  # host:container
```
- **Backend connects to**: `google-trends-mcp:8000` (internal port)
- **Host accesses via**: `localhost:8001` (external port)

**Why**: Containers communicate via internal network, not through host port mapping.

#### 3. **No localhost for inter-service communication**
```python
# ❌ WRONG
MCP_URL=http://localhost:8000

# ✅ CORRECT
MCP_URL=http://google-trends-mcp:8000
```
**Why**: `localhost` inside a container refers to that container's loopback, not other containers.

#### 4. **Health checks**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
```
**Why**: Health checks run *inside* the container, so `localhost` is correct here.

#### 5. **Dependency ordering**
```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy
```
**Why**: Ensures database is ready before backend starts, preventing connection errors.

---

## Summary

This architecture prioritizes:
- **Simplicity**: SSE over WebSocket, direct HTTP over complex adapters
- **Security**: JWT validation, RLS, middleware protection
- **Reliability**: Retry logic, health checks, proper error handling
- **Maintainability**: Clear separation of concerns, Docker networking best practices
