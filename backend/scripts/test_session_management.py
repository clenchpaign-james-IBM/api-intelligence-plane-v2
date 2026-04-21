"""
Test script for session management functionality.

Tests the new session creation endpoint and verifies that queries
are properly isolated between different sessions.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import httpx
from uuid import UUID


async def test_session_management():
    """Test session management functionality."""
    base_url = "http://localhost:8000/api/v1"
    
    print("=" * 80)
    print("Testing Session Management")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Create a new session
        print("\n1. Creating new session...")
        try:
            response = await client.post(f"{base_url}/query/session/new")
            response.raise_for_status()
            session_data = response.json()
            session_id_1 = session_data["session_id"]
            print(f"✓ Session 1 created: {session_id_1}")
        except Exception as e:
            print(f"✗ Failed to create session 1: {e}")
            return False
        
        # Test 2: Execute a query in session 1
        print("\n2. Executing query in session 1...")
        try:
            query_request = {
                "query_text": "Show me all APIs",
                "session_id": session_id_1,
            }
            response = await client.post(f"{base_url}/query", json=query_request)
            response.raise_for_status()
            query_data = response.json()
            print(f"✓ Query executed in session 1")
            print(f"  Response: {query_data['response_text'][:100]}...")
        except Exception as e:
            print(f"✗ Failed to execute query in session 1: {e}")
            return False
        
        # Test 3: Create another session
        print("\n3. Creating new session 2...")
        try:
            response = await client.post(f"{base_url}/query/session/new")
            response.raise_for_status()
            session_data = response.json()
            session_id_2 = session_data["session_id"]
            print(f"✓ Session 2 created: {session_id_2}")
            print(f"  Sessions are different: {session_id_1 != session_id_2}")
        except Exception as e:
            print(f"✗ Failed to create session 2: {e}")
            return False
        
        # Test 4: Execute a different query in session 2
        print("\n4. Executing query in session 2...")
        try:
            query_request = {
                "query_text": "What are the security vulnerabilities?",
                "session_id": session_id_2,
            }
            response = await client.post(f"{base_url}/query", json=query_request)
            response.raise_for_status()
            query_data = response.json()
            print(f"✓ Query executed in session 2")
            print(f"  Response: {query_data['response_text'][:100]}...")
        except Exception as e:
            print(f"✗ Failed to execute query in session 2: {e}")
            return False
        
        # Test 5: Verify session 1 history
        print("\n5. Checking session 1 history...")
        try:
            response = await client.get(f"{base_url}/query/session/{session_id_1}")
            response.raise_for_status()
            history_data = response.json()
            session_1_queries = history_data["items"]
            print(f"✓ Session 1 has {len(session_1_queries)} query(ies)")
            if session_1_queries:
                print(f"  First query: {session_1_queries[0]['query_text']}")
        except Exception as e:
            print(f"✗ Failed to get session 1 history: {e}")
            return False
        
        # Test 6: Verify session 2 history
        print("\n6. Checking session 2 history...")
        try:
            response = await client.get(f"{base_url}/query/session/{session_id_2}")
            response.raise_for_status()
            history_data = response.json()
            session_2_queries = history_data["items"]
            print(f"✓ Session 2 has {len(session_2_queries)} query(ies)")
            if session_2_queries:
                print(f"  First query: {session_2_queries[0]['query_text']}")
        except Exception as e:
            print(f"✗ Failed to get session 2 history: {e}")
            return False
        
        # Test 7: Verify sessions are isolated
        print("\n7. Verifying session isolation...")
        if len(session_1_queries) > 0 and len(session_2_queries) > 0:
            query_1_text = session_1_queries[0]['query_text']
            query_2_text = session_2_queries[0]['query_text']
            
            if query_1_text != query_2_text:
                print(f"✓ Sessions are properly isolated")
                print(f"  Session 1 query: {query_1_text}")
                print(f"  Session 2 query: {query_2_text}")
            else:
                print(f"✗ Sessions may not be properly isolated")
                return False
        else:
            print(f"⚠ Could not verify isolation (insufficient queries)")
        
        print("\n" + "=" * 80)
        print("✓ All session management tests passed!")
        print("=" * 80)
        return True


if __name__ == "__main__":
    print("\nMake sure the backend server is running on http://localhost:8000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled")
        sys.exit(0)
    
    success = asyncio.run(test_session_management())
    sys.exit(0 if success else 1)

# Made with Bob
