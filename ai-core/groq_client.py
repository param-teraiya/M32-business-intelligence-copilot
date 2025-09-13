import os
from typing import Dict, List, Optional, Any
from groq import Groq
from pydantic import BaseModel
from config import get_groq_api_key, get_model_name


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class GroqClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or get_groq_api_key()
        self.model_name = model_name or get_model_name()
        self.client = Groq(api_key=self.api_key)
        print(f"Groq client initialized with model: {self.model_name}")
        
        self.system_prompt = """You are M32 Business Intelligence Copilot, an AI assistant that helps small and medium business owners make better decisions.

You can help with:
- Market research and competitor analysis
- Business strategy and planning
- Industry trends and insights
- Financial analysis and forecasting
- Operations optimization

Keep responses practical and actionable. Use available tools when you need current information."""

    async def test_connection(self) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": "Test connection - respond with 'Connection successful'"}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            return {
                "status": "success",
                "model": self.model_name,
                "response": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": self.model_name
            }

    def create_chat_completion(
        self, 
        messages: List[ChatMessage], 
        max_tokens: int = 1024,
        temperature: float = 0.7,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        try:
            api_messages = [
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ]
            
            if not any(msg["role"] == "system" for msg in api_messages):
                api_messages.insert(0, {
                    "role": "system", 
                    "content": self.system_prompt
                })
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=api_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "status": "success",
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": self.model_name,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": self.model_name
            }

    def get_available_models(self) -> List[str]:
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            return [
                "mixtral-8x7b-32768",
                "llama2-70b-4096", 
                "gemma-7b-it"
            ]


groq_client = GroqClient()


async def test_groq_setup() -> None:
    print("Testing Groq connection...")
    
    result = await groq_client.test_connection()
    
    if result["status"] == "success":
        print(f"Connection OK - Model: {result['model']}")
        print(f"Response: {result['response']}")
    else:
        print(f"Connection failed: {result['error']}")
        print("Check your GROQ_API_KEY")
    
    print(f"Available models: {groq_client.get_available_models()}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_groq_setup())
