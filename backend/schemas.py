from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    company_name: Optional[str] = None
    industry: Optional[str] = None
    business_type: Optional[str] = None
    company_size: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    business_type: Optional[str] = None
    company_size: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    company_name: Optional[str] = None
    industry: Optional[str] = None
    business_type: Optional[str] = None
    company_size: Optional[str] = None
    
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: str = "email"
    is_google_user: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Google ID token")


class ChatMessageBase(BaseModel):
    content: str
    role: str = Field(..., pattern="^(user|assistant|system)$")


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: int
    created_at: datetime
    tools_used: Optional[List[str]] = None
    token_count: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ChatSessionBase(BaseModel):
    """Base chat session schema."""
    session_name: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    """Schema for creating chat sessions."""
    business_context: Optional[Dict[str, Any]] = None


class ChatSessionResponse(ChatSessionBase):
    """Schema for chat session response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    business_context: Optional[Dict[str, Any]] = None
    message_count: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    """Schema for chat requests."""
    message: str
    session_id: Optional[int] = None
    business_context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Schema for chat responses."""
    message: str
    response: str
    session_id: int
    tools_used: List[str] = []
    context_length: int
    created_at: datetime


# Business context schemas
class BusinessContext(BaseModel):
    """Schema for business context."""
    company_name: Optional[str] = None
    industry: Optional[str] = None
    business_type: Optional[str] = None
    company_size: Optional[str] = None
    current_challenges: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    target_market: Optional[str] = None


# API response schemas
class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    error_code: Optional[str] = None
    success: bool = False


# Health check schema
class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
