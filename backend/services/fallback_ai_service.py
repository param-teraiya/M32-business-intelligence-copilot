"""
Fallback AI Service for M32 Business Intelligence Copilot
Simple service that works without complex dependencies
"""

from typing import Dict, Any, Optional
import os
import json
import httpx
from datetime import datetime


class FallbackAIService:
    """Simple fallback AI service using direct Groq API calls."""
    
    def __init__(self):
        """Initialize the fallback service."""
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL_NAME", "mixtral-8x7b-32768")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    def is_available(self) -> bool:
        """Check if the service is available."""
        return bool(self.api_key)
    
    async def chat(self, message: str, session_id: str = "default", business_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a chat message to Groq API directly."""
        if not self.api_key:
            return {
                "status": "error",
                "response": "Groq API key not configured",
                "error": "Missing GROQ_API_KEY environment variable"
            }
        
        try:
            # Prepare system prompt
            system_prompt = """You are a Business Intelligence Copilot designed to help small and medium business owners make data-driven decisions.

Your role is to:
1. Analyze business situations and provide actionable insights
2. Help with strategic planning and decision-making
3. Provide market analysis and business recommendations
4. Translate complex concepts into clear, business-focused advice

Communication Style:
- Professional but approachable
- Clear and concise explanations
- Focus on actionable recommendations
- Structure responses with clear sections when appropriate

Remember: Your audience consists of business executives who value practical, results-oriented advice."""

            # Add business context to system prompt if available
            if business_context:
                context_info = []
                if business_context.get("company"):
                    context_info.append(f"Company: {business_context['company']}")
                if business_context.get("industry"):
                    context_info.append(f"Industry: {business_context['industry']}")
                if business_context.get("business_type"):
                    context_info.append(f"Business Type: {business_context['business_type']}")
                if business_context.get("company_size"):
                    context_info.append(f"Company Size: {business_context['company_size']}")
                
                if context_info:
                    system_prompt += f"\n\nBusiness Context:\n" + "\n".join(context_info)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Make API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 1,
                "stream": False
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    ai_response = result["choices"][0]["message"]["content"]
                    
                    return {
                        "status": "success",
                        "response": ai_response,
                        "session_id": session_id,
                        "context_length": len(messages),
                        "tools_used": [],
                        "token_count": result.get("usage", {}).get("total_tokens", 0)
                    }
                else:
                    return {
                        "status": "error",
                        "response": "No response from AI service",
                        "error": "Empty response from Groq API"
                    }
                    
        except httpx.TimeoutException:
            return {
                "status": "error",
                "response": "Request timed out. Please try again.",
                "error": "API request timeout"
            }
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "response": f"AI service error: {e.response.status_code}",
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            return {
                "status": "error",
                "response": f"Unexpected error: {str(e)}",
                "error": str(e)
            }


# Global fallback service instance
fallback_ai_service = FallbackAIService()