#!/usr/bin/env python3
"""
Quick Test Runner - Validates core functionality

Tests:
1. All modules import successfully
2. Configuration loads correctly
3. Snowflake connection works
4. Agent workflow executes
5. Conversation memory stores data

Usage: .venv/bin/python scripts/quick_test.py
"""

# Suppress Pydantic v1 compatibility warning for Python 3.14+
import warnings
warnings.filterwarnings('ignore', message='.*Pydantic V1 functionality.*')

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import Config
from src.agent import SQLAgent
from src.memory import ConversationMemory
from src.validator import SQLValidator
from src.tools import SnowflakeSQLTool
import snowflake.connector


def test_imports():
    """Test 1: Verify all imports work"""
    print("→ Testing imports...")
    try:
        from src.config import Config
        from src.agent import SQLAgent
        from src.tools import SnowflakeSQLTool
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_config():
    """Test 2: Verify configuration loads"""
    print("\n→ Testing configuration...")
    try:
        config = Config()
        sf_config = config.get_snowflake_config()
        openai_config = config.get_openai_config()
        
        assert sf_config['database'] == 'SNOWFLAKE_SAMPLE_DATA'
        assert sf_config['schema'] == 'TPCH_SF1'
        assert openai_config['api_key'].startswith('sk-')
        
        print(f"  ✓ Config loaded")
        print(f"    Database: {sf_config['database']}")
        print(f"    Schema: {sf_config['schema']}")
        return True
    except Exception as e:
        print(f"  ✗ Config failed: {e}")
        return False


def test_snowflake_connection():
    """Test 3: Verify Snowflake connection"""
    print("\n→ Testing Snowflake connection...")
    try:
        config = Config()
        sf_config = config.get_snowflake_config()
        
        conn = snowflake.connector.connect(**sf_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        assert result[0] == 1
        print("  ✓ Snowflake connection successful")
        return True
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False


def test_agent_simple_query():
    """Test 4: Run a simple query through the agent"""
    print("\n→ Testing agent with simple query...")
    try:
        config = Config()
        agent = SQLAgent(config)
        
        # Simple test query
        result = agent.run("How many rows are in the CUSTOMER table?")
        
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        print("  ✓ Agent executed successfully")
        print(f"    Generated {len(result['messages'])} messages")
        return True
    except Exception as e:
        print(f"  ✗ Agent failed: {e}")
        return False


def test_memory():
    """Test 5: Verify conversation memory works"""
    print("\n→ Testing conversation memory...")
    try:
        memory = ConversationMemory(":memory:")
        
        # Add test interaction
        memory.add_interaction(
            session_id="test_session",
            user_query="Test query",
            generated_sql="SELECT 1",
            result_summary="Test result"
        )
        
        # Retrieve history
        history = memory.get_recent_history("test_session", limit=1)
        
        assert len(history) == 1
        assert history[0]['user_query'] == "Test query"
        
        print("  ✓ Memory storage and retrieval working")
        return True
    except Exception as e:
        print(f"  ✗ Memory failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("QUICK FUNCTIONALITY TEST")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Snowflake Connection", test_snowflake_connection),
        ("Agent Query", test_agent_simple_query),
        ("Conversation Memory", test_memory)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Code is working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
