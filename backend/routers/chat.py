from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, AsyncGenerator
from datetime import datetime
import sys
import os
import json
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database import get_db, User, ChatSession, ChatMessage
from schemas import (
    ChatRequest, 
    ChatResponse, 
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageResponse,
    MessageResponse
)
from core.security import get_current_active_user

try:
    from services.groq_service import groq_service
    business_agent = groq_service
    print(f"Business agent loaded: {business_agent.is_available()}")
except ImportError as e:
    print(f"Could not import business agent: {e}")
    business_agent = None

router = APIRouter()


async def stream_ai_response(
    message: str,
    session_id: str,
    business_context: dict
) -> AsyncGenerator[str, None]:
    try:
        if not business_agent:
            yield f"data: {json.dumps({'error': 'AI service not available'})}\n\n"
            return
            
        if not business_agent.is_available():
            yield f"data: {json.dumps({'error': 'AI service not configured properly'})}\n\n"
            return
            
        ai_response = business_agent.chat(
            message=message,
            session_id=session_id,
            business_context=business_context
        )
        
        if ai_response["status"] != "success":
            yield f"data: {json.dumps({'error': ai_response.get('error', 'Unknown error')})}\n\n"
            return
        
        response_text = ai_response["response"]
        chunk_size = 15
        
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
            await asyncio.sleep(0.03)
        
        completion_data = {
            'done': True,
            'tools_used': ai_response.get('tools_used', []),
            'context_length': ai_response.get('context_length', 0),
            'token_count': ai_response.get('token_count', 0)
        }
        yield f"data: {json.dumps(completion_data)}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}'})}\n\n"


@router.post("/stream")
async def stream_chat_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not business_agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )
    
    session = None
    if chat_request.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == chat_request.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.is_active == True
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        session = ChatSession(
            user_id=current_user.id,
            session_name=f"Chat {len(current_user.chat_sessions) + 1}",
            is_active=True
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    
    business_context = chat_request.business_context or {}
    if current_user.company_name:
        business_context["company"] = current_user.company_name
    if current_user.industry:
        business_context["industry"] = current_user.industry
    if current_user.business_type:
        business_context["business_type"] = current_user.business_type
    if current_user.company_size:
        business_context["company_size"] = current_user.company_size
    
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    
    return StreamingResponse(
        stream_ai_response(
            message=chat_request.message,
            session_id=f"session_{session.id}",
            business_context=business_context
        ),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    session = None
    if chat_request.session_id:
        # Get existing session
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == chat_request.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.is_active == True
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        # Create new session
        session = ChatSession(
            user_id=current_user.id,
            session_name=f"Chat Session {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            is_active=True
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    
    # Prepare business context
    business_context = chat_request.business_context or {}
    
    # Add user's business profile to context
    if current_user.company_name:
        business_context["company"] = current_user.company_name
    if current_user.industry:
        business_context["industry"] = current_user.industry
    if current_user.business_type:
        business_context["business_type"] = current_user.business_type
    if current_user.company_size:
        business_context["company_size"] = current_user.company_size
    
    # Update session business context
    session.set_business_context(business_context)
    
    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    
    try:
        # Check if AI service is available
        if not business_agent:
            # Return a helpful error message instead of crashing
            ai_response = {
                "status": "success",
                "response": "I apologize, but the AI service is currently unavailable. This might be due to:\n\n1. Missing Groq API key configuration\n2. Import issues with the AI modules\n3. Service initialization problems\n\nPlease check your environment configuration and ensure the Groq API key is properly set.",
                "tools_used": [],
                "context_length": 0,
                "token_count": 0
            }
        elif not business_agent.is_available():
            ai_response = {
                "status": "success", 
                "response": "The AI service is not properly configured. Please check your Groq API key in the environment variables.",
                "tools_used": [],
                "context_length": 0,
                "token_count": 0
            }
        else:
            # Use the async chat method
            ai_response = await business_agent.chat(
                message=chat_request.message,
                session_id=f"session_{session.id}",
                business_context=business_context
            )
            
            if ai_response["status"] != "success":
                # Convert error to a user-friendly message
                ai_response = {
                    "status": "success",
                    "response": f"I encountered an issue processing your request: {ai_response.get('error', 'Unknown error')}. Please try again or contact support if the problem persists.",
                    "tools_used": [],
                    "context_length": 0,
                    "token_count": 0
                }
        
        # Save AI response
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=ai_response["response"],
            token_count=ai_response.get("token_count")
        )
        assistant_message.set_tools_used(ai_response.get("tools_used", []))
        db.add(assistant_message)
        
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)
        
        return ChatResponse(
            message=chat_request.message,
            response=ai_response["response"],
            session_id=session.id,
            tools_used=ai_response.get("tools_used", []),
            context_length=ai_response.get("context_length", 0),
            created_at=assistant_message.created_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chat sessions for the current user.
    """
    # Get sessions with message count
    result = await db.execute(
        select(
            ChatSession,
            func.count(ChatMessage.id).label("message_count")
        )
        .outerjoin(ChatMessage)
        .where(ChatSession.user_id == current_user.id)
        .group_by(ChatSession.id)
        .order_by(desc(ChatSession.updated_at))
    )
    
    sessions = []
    for session, message_count in result.all():
        session_dict = {
            "id": session.id,
            "user_id": session.user_id,
            "session_name": session.session_name,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "is_active": session.is_active,
            "business_context": session.get_business_context(),
            "message_count": message_count or 0
        }
        sessions.append(session_dict)
    
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific chat session.
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get message count
    message_count_result = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session_id)
    )
    message_count = message_count_result.scalar() or 0
    
    return {
        "id": session.id,
        "user_id": session.user_id,
        "session_name": session.session_name,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "is_active": session.is_active,
        "business_context": session.get_business_context(),
        "message_count": message_count
    }


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all messages for a specific chat session.
    """
    # Verify session belongs to user
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get messages
    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()
    
    return [
        {
            "id": msg.id,
            "content": msg.content,
            "role": msg.role,
            "created_at": msg.created_at,
            "tools_used": msg.get_tools_used(),
            "token_count": msg.token_count
        }
        for msg in messages
    ]


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chat session.
    """
    session = ChatSession(
        user_id=current_user.id,
        session_name=session_data.session_name or f"New Chat",
        is_active=True
    )
    
    if session_data.business_context:
        session.set_business_context(session_data.business_context)
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return {
        "id": session.id,
        "user_id": session.user_id,
        "session_name": session.session_name,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "is_active": session.is_active,
        "business_context": session.get_business_context(),
        "message_count": 0
    }


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: int,
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a chat session (e.g., rename).
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Update session fields
    if session_data.session_name is not None:
        session.session_name = session_data.session_name
    if session_data.business_context is not None:
        session.set_business_context(session_data.business_context)
    
    await db.commit()
    await db.refresh(session)
    
    # Get message count
    message_count_result = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session_id)
    )
    message_count = message_count_result.scalar() or 0
    
    return {
        "id": session.id,
        "user_id": session.user_id,
        "session_name": session.session_name,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "is_active": session.is_active,
        "business_context": session.get_business_context(),
        "message_count": message_count
    }


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a chat session (soft delete).
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    session.is_active = False
    await db.commit()
    
    return {
        "message": "Chat session deleted successfully",
        "success": True
    }
