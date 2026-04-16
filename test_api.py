"""Example test cases for the AI Assistant API"""

import asyncio
import httpx


async def test_health():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_root():
    """Test root endpoint"""
    print("\n=== Testing Root Endpoint ===")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_available_models():
    """Test available models endpoint"""
    print("\n=== Testing Available Models ===")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/models")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_chat_simple():
    """Test simple chat request"""
    print("\n=== Testing Chat (OpenAI - requires API key) ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "What is 2+2?"}
                    ],
                    "model": "openai",
                    "temperature": 0.7,
                    "max_tokens": 100
                },
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_chat_with_history():
    """Test chat with conversation history"""
    print("\n=== Testing Chat with History ===")
    async with httpx.AsyncClient() as client:
        messages = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "What can I use it for?"}
        ]
        
        try:
            response = await client.post(
                "http://localhost:8000/api/chat",
                json={
                    "messages": messages,
                    "model": "openai",
                    "temperature": 0.7,
                    "max_tokens": 200
                },
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_memory():
    """Test memory endpoints"""
    print("\n=== Testing Memory Endpoints ===")
    async with httpx.AsyncClient() as client:
        # Get memory
        response = await client.get("http://localhost:8000/api/memory?limit=5")
        print(f"Get Memory Status: {response.status_code}")
        print(f"Memory: {response.json()}")


async def main():
    """Run all tests"""
    print("=" * 50)
    print("AI Assistant API - Test Suite")
    print("=" * 50)
    print("\nMake sure the server is running: python main.py")
    
    try:
        # Test endpoints that don't require API keys
        await test_health()
        await test_root()
        await test_available_models()
        await test_memory()
        
        # Test chat endpoints (may fail without API keys)
        await test_chat_simple()
        await test_chat_with_history()
        
        print("\n" + "=" * 50)
        print("✓ Tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
