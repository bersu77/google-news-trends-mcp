
import asyncio
import httpx
import json
import sys

BASE_URL = "http://localhost:8000/api"
EMAIL = "dawitworkye21@gmail.com"
PASSWORD = "password123"

from jose import jwt
from datetime import datetime, timedelta

# ...

SECRET_KEY = "app_secret_key_7X3nQ9pL2kR5vM8wS1tY6uJ4fZ9cX5bA0dE3gH7iK1oP4nM8jV2sW5rT9yU6fZ"
ALGORITHM = "HS256"

async def get_token():
    print("Generating self-signed test token...")
    payload = {
        "sub": "test-user-id",
        "email": EMAIL,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "aud": "authenticated"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

async def run_chat_test(token, prompt, test_name):
    print(f"\n--- Testing: {test_name} ---")
    print(f"Prompt: {prompt}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", f"{BASE_URL}/chat/stream", json={"message": prompt, "conversation_id": None}, headers=headers) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                # print(await response.read())
                return

            print("Stream Response:")
            tool_used = False
            final_answer = ""
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        msg_type = data.get("type")
                        if not msg_type:
                            # print(f"Warning: No type in data: {data}")
                            continue
                            
                        if msg_type == "token":
                            print(data["token"], end="", flush=True)
                            final_answer += data["token"]
                        elif msg_type == "tool_call" or (data.get("tool_calls")):
                             # Frontend receives type='content' with tool_calls populated at end
                             # But mid-stream we might get 'activity'
                             pass
                        elif msg_type == "activity":
                             print(f"\n[ACTIVITY: {data['content']}]")
                             tool_used = True
                    except json.JSONDecodeError:
                        pass
            print("\n------------------------------------------------")

async def main():
    token = await get_token()
    if not token:
        print("Could not get auth token. Exiting.")
        return

    # TOOL-01: Tavily search
    await run_chat_test(token, "Find what Tavily API does", "TOOL-01: Tavily Search")
    
    # TOOL-02: Google Trends MCP
    await run_chat_test(token, "Check Google Trends for 'AI agents'", "TOOL-02: Google Trends")

    # TOOL-03: Correct tool selection (SSE)
    await run_chat_test(token, "What is SSE streaming?", "TOOL-03: No Tool Expected")
    
    print("\nTests 1-3 Complete. For TOOL-04, please stop the MCP container and run this script again with only the trends test.")

if __name__ == "__main__":
    asyncio.run(main())
