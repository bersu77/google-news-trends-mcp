
import asyncio
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print(f"Testing connection to: {url}")

async def test_connection():
    try:
        # Test 1: Direct HTTP access to verify SSL/Network layer
        print("\nTest 1: Direct HTTP GET to Supabase URL...")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            print(f"Direct HTTP Status: {resp.status_code}")
    except Exception as e:
        print(f"Direct HTTP Failed: {e}")

    try:
        # Test 2: Supabase Client
        print("\nTest 2: Supabase Client Query...")
        supabase: Client = create_client(url, key)
        response = supabase.table("conversations").select("id").limit(1).execute()
        print("Supabase data retrieved successfully!")
        print(response)
    except Exception as e:
        print(f"Supabase Client Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
