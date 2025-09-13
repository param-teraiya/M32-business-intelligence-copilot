import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()
print("Loading configuration...")


class Settings(BaseSettings):
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY")
    groq_model_name: str = Field("openai/gpt-oss-120b", env="GROQ_MODEL_NAME")
    
    available_models: list[str] = [
        "openai/gpt-oss-120b",
        "meta-llama/llama-3.2-90b-vision-preview",
        "meta-llama/llama-3.2-11b-vision-preview",
        "meta-llama/llama-3.1-70b-versatile",
        "meta-llama/llama-3.1-8b-instant",
    ]
    
    max_tokens: int = Field(1024, env="MAX_TOKENS")
    temperature: float = Field(0.7, env="TEMPERATURE")
    max_conversation_history: int = Field(10, env="MAX_CONVERSATION_HISTORY")
    debug: bool = Field(False, env="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_groq_api_key() -> str:
    api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
    
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY must be set in .env file or environment variables.\n"
            "Please copy .env.example to .env and add your API key."
        )
    return api_key


def get_model_name() -> str:
    return settings.groq_model_name


def is_debug_mode() -> bool:
    return settings.debug


def validate_config() -> dict:
    try:
        api_key = get_groq_api_key()
        return {
            "status": "valid",
            "api_key_configured": True,
            "api_key_preview": f"{api_key[:10]}..." if len(api_key) > 10 else "***",
            "model_name": get_model_name(),
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "debug_mode": is_debug_mode()
        }
    except ValueError as e:
        return {
            "status": "invalid",
            "api_key_configured": False,
            "error": str(e),
            "model_name": get_model_name(),
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "debug_mode": is_debug_mode()
        }


def print_config_status():
    config_status = validate_config()
    
    print("=" * 40)
    print("M32 BI COPILOT - CONFIG STATUS")
    print("=" * 40)
    
    if config_status["status"] == "valid":
        print("Config OK!")
        print(f"API Key: {config_status['api_key_preview']}")
        print(f"Model: {config_status['model_name']}")
        print(f"Max Tokens: {config_status['max_tokens']}")
        print(f"Temperature: {config_status['temperature']}")
        print(f"Debug: {config_status['debug_mode']}")
    else:
        print("Config Error!")
        print(f"Error: {config_status['error']}")
        print(f"Model: {config_status['model_name']}")
        print(f"Debug: {config_status['debug_mode']}")
        print("\nFix:")
        print("1. Copy .env.example to .env")
        print("2. Add your Groq API key")
    
    print("=" * 40)


if __name__ == "__main__":
    print_config_status()
