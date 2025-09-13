"""
Groq AI Service for M32 Business Intelligence Copilot
"""

import sys
import os
from typing import Dict, Any, Optional

# Add ai-core and tools to path
current_dir = os.path.dirname(__file__)
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
ai_core_path = os.path.join(project_root, 'ai-core')
tools_path = os.path.join(project_root, 'tools')

sys.path.insert(0, ai_core_path)
sys.path.insert(0, tools_path)

# Also try the Docker mounted paths
sys.path.insert(0, '/app/ai-core')
sys.path.insert(0, '/app/tools')

try:
    from langchain_integration import BusinessIntelligenceAgent
    print("✅ Successfully imported BusinessIntelligenceAgent")
except ImportError as e:
    print(f"Warning: Could not import BusinessIntelligenceAgent: {e}")
    print(f"Python path: {sys.path}")
    print(f"AI core path exists: {os.path.exists(ai_core_path)}")
    print(f"Files in ai-core: {os.listdir(ai_core_path) if os.path.exists(ai_core_path) else 'Directory not found'}")
    BusinessIntelligenceAgent = None


class GroqService:
    """Service for Groq AI integration with fallback support."""
    
    def __init__(self):
        """Initialize the Groq service."""
        self.agent = None
        self.fallback = None
        
        # Try to initialize the main agent
        if BusinessIntelligenceAgent:
            try:
                self.agent = BusinessIntelligenceAgent()
                print("✅ GroqService initialized successfully")
            except Exception as e:
                print(f"⚠️ GroqService initialization failed: {e}")
                self.agent = None
        else:
            print("⚠️ BusinessIntelligenceAgent not available")
        
        # Initialize fallback service
        try:
            from .fallback_ai_service import fallback_ai_service
            self.fallback = fallback_ai_service
            print("✅ Fallback AI service initialized")
        except Exception as e:
            print(f"⚠️ Fallback service initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if any service is available."""
        return (self.agent is not None) or (self.fallback is not None and self.fallback.is_available())
    
    async def chat(self, message: str, session_id: str = "default", business_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a chat message to the AI agent with fallback support."""
        # Try main agent first
        if self.agent:
            try:
                return self.agent.chat(message, session_id, business_context)
            except Exception as e:
                print(f"Main agent failed, trying fallback: {e}")
        
        # Use fallback service
        if self.fallback and self.fallback.is_available():
            try:
                return await self.fallback.chat(message, session_id, business_context)
            except Exception as e:
                return {
                    "status": "error",
                    "response": f"Both AI services failed: {str(e)}",
                    "error": str(e)
                }
        
        return {
            "status": "error",
            "response": "AI service is not available",
            "error": "No AI service available"
        }


# Global instance
groq_service = GroqService()