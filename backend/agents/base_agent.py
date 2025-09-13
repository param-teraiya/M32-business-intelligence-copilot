"""
Base Agent class for M32 Business Intelligence System
Provides common functionality for all AI agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for AI agents."""
    name: str
    description: str
    max_context_length: int = 4000
    temperature: float = 0.7
    max_tokens: int = 1024
    tools_enabled: List[str] = []


class AgentMessage(BaseModel):
    """Standard message format for agents."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}


class AgentContext(BaseModel):
    """Context management for agent conversations."""
    session_id: str
    messages: List[AgentMessage] = []
    business_context: Dict[str, Any] = {}
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the context."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[AgentMessage]:
        """Get recent messages with limit."""
        return self.messages[-limit:] if limit > 0 else self.messages
    
    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages = []
        self.updated_at = datetime.now()


class BaseAgent(ABC):
    """
    Abstract base class for all M32 AI agents.
    Provides common functionality and interface.
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the base agent."""
        self.config = config
        self.contexts: Dict[str, AgentContext] = {}
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        
    def get_or_create_context(self, session_id: str, business_context: Dict[str, Any] = None) -> AgentContext:
        """Get existing context or create new one."""
        if session_id not in self.contexts:
            self.contexts[session_id] = AgentContext(
                session_id=session_id,
                business_context=business_context or {}
            )
        elif business_context:
            # Update business context if provided
            self.contexts[session_id].business_context.update(business_context)
            self.contexts[session_id].updated_at = datetime.now()
            
        return self.contexts[session_id]
    
    def add_message_to_context(self, session_id: str, message: AgentMessage) -> None:
        """Add message to context."""
        context = self.get_or_create_context(session_id)
        context.add_message(message)
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[AgentMessage]:
        """Get conversation history for a session."""
        if session_id in self.contexts:
            return self.contexts[session_id].get_recent_messages(limit)
        return []
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session."""
        if session_id in self.contexts:
            self.contexts[session_id].clear_messages()
            return True
        return False
    
    def delete_context(self, session_id: str) -> bool:
        """Delete entire context for a session."""
        if session_id in self.contexts:
            del self.contexts[session_id]
            return True
        return False
    
    @abstractmethod
    async def process_message(
        self,
        message: str,
        session_id: str,
        business_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a message and return response.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tools for this agent.
        Must be implemented by subclasses.
        """
        pass
    
    def validate_input(self, message: str) -> bool:
        """Validate input message."""
        if not message or not message.strip():
            return False
        if len(message) > 10000:  # Max message length
            return False
        return True
    
    def format_error_response(self, error: str, session_id: str) -> Dict[str, Any]:
        """Format error response."""
        return {
            "status": "error",
            "error": error,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
    
    def format_success_response(
        self,
        response: str,
        session_id: str,
        tools_used: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Format success response."""
        return {
            "status": "success",
            "response": response,
            "session_id": session_id,
            "tools_used": tools_used or [],
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
    
    def log_interaction(
        self,
        session_id: str,
        message: str,
        response: str,
        tools_used: List[str] = None
    ) -> None:
        """Log agent interaction for monitoring."""
        self.logger.info(
            f"Agent interaction - Session: {session_id}, "
            f"Message length: {len(message)}, "
            f"Response length: {len(response)}, "
            f"Tools used: {tools_used or []}"
        )
