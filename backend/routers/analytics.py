"""
Analytics router for M32 Business Intelligence System
Provides usage metrics, performance stats, and business insights.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from database import get_db, User, ChatSession, ChatMessage
from schemas import AnalyticsResponse, UsageStatsResponse, MessageResponse
from core.security import get_current_active_user, verify_admin_user
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive analytics dashboard data.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        # User's personal analytics
        user_stats = await _get_user_analytics(db, current_user.id, start_date, end_date)
        
        # System-wide analytics (if admin)
        system_stats = {}
        if current_user.is_admin:
            system_stats = await _get_system_analytics(db, start_date, end_date)
        
        return {
            "user_analytics": user_stats,
            "system_analytics": system_stats,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics dashboard"
        )


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_statistics(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed usage statistics for the current user.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        # Chat sessions count
        sessions_result = await db.execute(
            select(func.count(ChatSession.id))
            .where(
                and_(
                    ChatSession.user_id == current_user.id,
                    ChatSession.created_at >= start_date,
                    ChatSession.created_at <= end_date
                )
            )
        )
        total_sessions = sessions_result.scalar() or 0
        
        # Messages count
        messages_result = await db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession)
            .where(
                and_(
                    ChatSession.user_id == current_user.id,
                    ChatMessage.created_at >= start_date,
                    ChatMessage.created_at <= end_date
                )
            )
        )
        total_messages = messages_result.scalar() or 0
        
        # Average messages per session
        avg_messages = total_messages / total_sessions if total_sessions > 0 else 0
        
        # Token usage (if available)
        token_result = await db.execute(
            select(func.sum(ChatMessage.token_count))
            .join(ChatSession)
            .where(
                and_(
                    ChatSession.user_id == current_user.id,
                    ChatMessage.created_at >= start_date,
                    ChatMessage.created_at <= end_date,
                    ChatMessage.token_count.isnot(None)
                )
            )
        )
        total_tokens = token_result.scalar() or 0
        
        # Most active days
        daily_activity = await db.execute(
            select(
                func.date(ChatMessage.created_at).label("date"),
                func.count(ChatMessage.id).label("message_count")
            )
            .join(ChatSession)
            .where(
                and_(
                    ChatSession.user_id == current_user.id,
                    ChatMessage.created_at >= start_date,
                    ChatMessage.created_at <= end_date
                )
            )
            .group_by(func.date(ChatMessage.created_at))
            .order_by(desc("message_count"))
            .limit(5)
        )
        
        activity_data = [
            {
                "date": row.date.isoformat(),
                "message_count": row.message_count
            }
            for row in daily_activity.all()
        ]
        
        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "avg_messages_per_session": round(avg_messages, 2),
            "daily_activity": activity_data,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Usage statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate usage statistics"
        )


@router.get("/tools", response_model=Dict[str, Any])
async def get_tool_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics on tool usage patterns.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        # Get messages with tools used
        messages_result = await db.execute(
            select(ChatMessage.tools_used, ChatMessage.created_at)
            .join(ChatSession)
            .where(
                and_(
                    ChatSession.user_id == current_user.id,
                    ChatMessage.created_at >= start_date,
                    ChatMessage.created_at <= end_date,
                    ChatMessage.tools_used.isnot(None)
                )
            )
        )
        
        # Analyze tool usage
        tool_counts = {}
        tool_combinations = {}
        
        for row in messages_result.all():
            if row.tools_used:
                try:
                    tools = json.loads(row.tools_used) if isinstance(row.tools_used, str) else row.tools_used
                    if isinstance(tools, list):
                        # Count individual tools
                        for tool in tools:
                            tool_counts[tool] = tool_counts.get(tool, 0) + 1
                        
                        # Count tool combinations
                        if len(tools) > 1:
                            combo_key = ", ".join(sorted(tools))
                            tool_combinations[combo_key] = tool_combinations.get(combo_key, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Sort by usage
        sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
        sorted_combinations = sorted(tool_combinations.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "period_days": days,
            "tool_usage": dict(sorted_tools),
            "popular_combinations": dict(list(sorted_combinations)[:10]),
            "total_tool_calls": sum(tool_counts.values()),
            "unique_tools_used": len(tool_counts),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Tool analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate tool analytics"
        )


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics(
    current_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system performance metrics (admin only).
    """
    try:
        # Recent system activity (last 24 hours)
        last_24h = datetime.now() - timedelta(hours=24)
        
        # Total users
        total_users = await db.execute(select(func.count(User.id)))
        total_users = total_users.scalar()
        
        # Active users (last 24h)
        active_users = await db.execute(
            select(func.count(func.distinct(ChatSession.user_id)))
            .where(ChatSession.created_at >= last_24h)
        )
        active_users = active_users.scalar()
        
        # Total sessions and messages
        total_sessions = await db.execute(select(func.count(ChatSession.id)))
        total_sessions = total_sessions.scalar()
        
        total_messages = await db.execute(select(func.count(ChatMessage.id)))
        total_messages = total_messages.scalar()
        
        # Recent activity
        recent_sessions = await db.execute(
            select(func.count(ChatSession.id))
            .where(ChatSession.created_at >= last_24h)
        )
        recent_sessions = recent_sessions.scalar()
        
        recent_messages = await db.execute(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.created_at >= last_24h)
        )
        recent_messages = recent_messages.scalar()
        
        # Average response time (placeholder - would need actual timing data)
        avg_response_time = 2.5  # seconds
        
        return {
            "system_health": {
                "status": "healthy",
                "uptime": "99.9%",  # Placeholder
                "avg_response_time": avg_response_time
            },
            "user_metrics": {
                "total_users": total_users,
                "active_users_24h": active_users,
                "user_activity_rate": round((active_users / total_users * 100), 2) if total_users > 0 else 0
            },
            "usage_metrics": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "recent_sessions_24h": recent_sessions,
                "recent_messages_24h": recent_messages,
                "messages_per_session": round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate performance metrics"
        )


async def _get_user_analytics(
    db: AsyncSession,
    user_id: int,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """Get analytics data for a specific user."""
    
    # Sessions created
    sessions_result = await db.execute(
        select(func.count(ChatSession.id))
        .where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            )
        )
    )
    sessions_count = sessions_result.scalar() or 0
    
    # Messages sent
    messages_result = await db.execute(
        select(func.count(ChatMessage.id))
        .join(ChatSession)
        .where(
            and_(
                ChatSession.user_id == user_id,
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date,
                ChatMessage.role == "user"
            )
        )
    )
    messages_count = messages_result.scalar() or 0
    
    # Most used business context
    context_result = await db.execute(
        select(ChatSession.business_context)
        .where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date,
                ChatSession.business_context.isnot(None)
            )
        )
    )
    
    industries = {}
    for row in context_result.all():
        if row.business_context:
            try:
                context = json.loads(row.business_context) if isinstance(row.business_context, str) else row.business_context
                industry = context.get("industry")
                if industry:
                    industries[industry] = industries.get(industry, 0) + 1
            except (json.JSONDecodeError, TypeError):
                continue
    
    top_industry = max(industries.items(), key=lambda x: x[1])[0] if industries else None
    
    return {
        "sessions_created": sessions_count,
        "messages_sent": messages_count,
        "avg_messages_per_session": round(messages_count / sessions_count, 2) if sessions_count > 0 else 0,
        "top_industry": top_industry,
        "industry_distribution": dict(sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5])
    }


async def _get_system_analytics(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """Get system-wide analytics data."""
    
    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    # New users in period
    new_users_result = await db.execute(
        select(func.count(User.id))
        .where(
            and_(
                User.created_at >= start_date,
                User.created_at <= end_date
            )
        )
    )
    new_users = new_users_result.scalar() or 0
    
    # Active users in period
    active_users_result = await db.execute(
        select(func.count(func.distinct(ChatSession.user_id)))
        .where(
            and_(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            )
        )
    )
    active_users = active_users_result.scalar() or 0
    
    # Total sessions in period
    sessions_result = await db.execute(
        select(func.count(ChatSession.id))
        .where(
            and_(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            )
        )
    )
    total_sessions = sessions_result.scalar() or 0
    
    return {
        "total_users": total_users,
        "new_users": new_users,
        "active_users": active_users,
        "total_sessions": total_sessions,
        "user_engagement_rate": round((active_users / total_users * 100), 2) if total_users > 0 else 0
    }
