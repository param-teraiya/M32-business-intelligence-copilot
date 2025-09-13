"""
M32 AI Core Module
Contains the core AI functionality including Groq integration and business intelligence agent.
"""

from .langchain_integration import BusinessIntelligenceAgent
from .groq_client import groq_client, ChatMessage
from .config import settings, get_groq_api_key, get_model_name

__all__ = [
    'BusinessIntelligenceAgent',
    'groq_client', 
    'ChatMessage',
    'settings',
    'get_groq_api_key',
    'get_model_name'
]
