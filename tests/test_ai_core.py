"""
Test script for the AI core functionality.
Validates Groq integration, LangChain setup, and tool functionality.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ai-core"))
sys.path.insert(0, str(project_root / "backend"))

try:
    from ai_core.groq_client import GroqClient, ChatMessage
    from ai_core.config import validate_config
    from ai_core.langchain_integration import BusinessIntelligenceAgent, test_langchain_integration
    from tools.web_search import web_search_business
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running this script from the project root directory.")
    sys.exit(1)


async def test_complete_ai_pipeline():
    """Test the complete AI pipeline with business scenarios."""
    print("=" * 60)
    print("M32 BUSINESS INTELLIGENCE COPILOT - AI CORE TEST")
    print("=" * 60)
    
    # Check configuration
    try:
        config_status = validate_config()
        
        if config_status["status"] != "valid":
            print("⚠️  Configuration invalid!")
            print(f"Error: {config_status['error']}")
            print("\nTo fix this:")
            print("1. Run: python setup_production_env.py (create environment files)")
            print("2. Edit .env files with your actual API keys")
            print("3. Run: python scripts/setup_env.py (guided setup)")
            return
        
        print(f"🔑 API Key configured: {config_status['api_key_preview']}")
        print(f"🤖 Model: {config_status['model_name']}")
    except Exception as e:
        print(f"⚠️  Configuration check failed: {e}")
        print("Please ensure your environment is properly configured.")
        return
    
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize components
    groq_client = GroqClient()
    business_agent = BusinessIntelligenceAgent()
    
    # Test 1: Groq API Connection
    print("\n" + "=" * 40)
    print("TEST 1: GROQ API CONNECTION")
    print("=" * 40)
    
    try:
        messages = [ChatMessage(role="user", content="Hello, are you working?")]
        result = groq_client.create_chat_completion(messages, temperature=0.7)
        
        if result["status"] == "success":
            print("✅ Groq API connection successful!")
            print(f"Response: {result['content'][:100]}...")
        else:
            print(f"❌ Groq API connection failed: {result['error']}")
    except Exception as e:
        print(f"❌ Groq API test failed: {e}")
    
    # Test 2: Web Search Tool
    print("\n" + "=" * 40)
    print("TEST 2: WEB SEARCH TOOL")
    print("=" * 40)
    
    try:
        search_result = web_search_business("AI trends 2024")
        if search_result and len(search_result) > 50:
            print("✅ Web search tool working!")
            print(f"Search result preview: {search_result[:150]}...")
        else:
            print("⚠️  Web search returned limited results")
    except Exception as e:
        print(f"❌ Web search test failed: {e}")
    
    # Test 3: Direct Groq Chat
    print("\n" + "=" * 40)
    print("TEST 3: DIRECT GROQ CHAT")
    print("=" * 40)
    
    try:
        messages = [
            ChatMessage(role="user", content="What are the key challenges facing small businesses in 2024?")
        ]
        
        result = groq_client.create_chat_completion(messages, temperature=0.7)
        
        if result["status"] == "success":
            print("✅ Direct chat successful!")
            print(f"Response: {result['content'][:300]}...")
            if 'usage' in result:
                print(f"Tokens used: {result['usage'].get('total_tokens', 'N/A')}")
        else:
            print(f"❌ Direct chat failed: {result['error']}")
    except Exception as e:
        print(f"❌ Direct chat test failed: {e}")
    
    # Test 4: Business Agent Integration
    print("\n" + "=" * 40)
    print("TEST 4: BUSINESS AGENT INTEGRATION")
    print("=" * 40)
    
    try:
        if hasattr(business_agent, 'is_available') and business_agent.is_available():
            print("✅ Business agent is available!")
        else:
            print("⚠️  Business agent may not be properly configured")
            
        # Test basic functionality
        test_result = business_agent.chat(
            "What are current SaaS industry trends?",
            session_id="test_session"
        )
        
        if test_result["status"] == "success":
            print("✅ Business agent chat successful!")
            print(f"Response preview: {test_result['response'][:200]}...")
        else:
            print(f"❌ Business agent chat failed: {test_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Business agent test failed: {e}")
    
    # Test 5: Business Scenarios
    print("\n" + "=" * 40)
    print("TEST 5: BUSINESS SCENARIOS")
    print("=" * 40)
    
    business_scenarios = [
        {
            "query": "I run a small e-commerce business selling handmade jewelry. What are the current market trends I should know about?",
            "context": {"industry": "e-commerce", "business_type": "handmade jewelry"}
        },
        {
            "query": "Who are my main competitors and how can I differentiate my business?",
            "context": {"company": "handmade jewelry business", "industry": "e-commerce"}
        }
    ]
    
    for i, scenario in enumerate(business_scenarios, 1):
        print(f"\nScenario {i}: {scenario['query'][:60]}...")
        
        try:
            result = business_agent.chat(
                scenario["query"],
                session_id=f"test_scenario_{i}",
                business_context=scenario["context"]
            )
            
            if result["status"] == "success":
                print(f"✅ Scenario {i} successful!")
                print(f"Response length: {len(result['response'])} characters")
                print(f"Tools used: {result.get('tools_used', [])}")
                print(f"Preview: {result['response'][:150]}...")
            else:
                print(f"❌ Scenario {i} failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Scenario {i} failed with exception: {e}")
    
    # Test 6: Context Management
    print("\n" + "=" * 40)
    print("TEST 6: CONTEXT MANAGEMENT")
    print("=" * 40)
    
    try:
        # First message
        result1 = business_agent.chat(
            "My company name is ArtisanCraft and we make handmade jewelry.",
            session_id="context_test"
        )
        
        if result1["status"] == "success":
            print("✅ First context message successful!")
            
            # Follow-up that requires context
            result2 = business_agent.chat(
                "What marketing strategies would work best for my company?",
                session_id="context_test"
            )
            
            if result2["status"] == "success":
                print("✅ Context management working!")
                print(f"Context length: {result2.get('context_length', 'N/A')} messages")
            else:
                print(f"❌ Context follow-up failed: {result2.get('error', 'Unknown error')}")
        else:
            print(f"❌ First context message failed: {result1.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Context management test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 AI CORE TESTING COMPLETE")
    print("=" * 60)
    print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def run_quick_test():
    """Run a quick test of core functionality."""
    print("Quick AI Core Test")
    print("-" * 30)
    
    try:
        # Initialize business agent
        business_agent = BusinessIntelligenceAgent()
        
        # Test basic chat
        result = business_agent.chat(
            "Hello! Can you help me understand current business trends?",
            session_id="quick_test"
        )
        
        if result["status"] == "success":
            print("✅ Quick test successful!")
            print(f"Response: {result['response'][:200]}...")
        else:
            print(f"❌ Quick test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Quick test failed with exception: {e}")


if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Complete AI Pipeline Test (comprehensive)")
    print("2. Quick Test (basic functionality)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_complete_ai_pipeline())
    elif choice == "2":
        run_quick_test()
    else:
        print("Invalid choice. Running quick test...")
        run_quick_test()
