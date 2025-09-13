"""
Logging utilities for M32 Business Intelligence System
Provides structured logging for production deployment.
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import os


class BusinessIntelligenceFormatter(logging.Formatter):
    """Custom formatter for business intelligence logs."""
    
    def format(self, record):
        # Add timestamp
        record.timestamp = datetime.now().isoformat()
        
        # Add service context
        if not hasattr(record, 'service'):
            record.service = 'M32-BI'
        
        # Format message
        if record.levelno >= logging.ERROR:
            format_string = "[{timestamp}] {service} ERROR {name}: {message}"
        elif record.levelno >= logging.WARNING:
            format_string = "[{timestamp}] {service} WARN {name}: {message}"
        else:
            format_string = "[{timestamp}] {service} INFO {name}: {message}"
        
        return format_string.format(
            timestamp=record.timestamp,
            service=record.service,
            name=record.name,
            message=record.getMessage()
        )


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger for the business intelligence system.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Don't add handlers if already configured
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Set formatter
    formatter = BusinessIntelligenceFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def log_business_interaction(
    logger: logging.Logger,
    session_id: str,
    user_message: str,
    ai_response: str,
    tools_used: list = None,
    execution_time: float = None
):
    """
    Log a business intelligence interaction.
    
    Args:
        logger: Logger instance
        session_id: Session identifier
        user_message: User's input message
        ai_response: AI's response
        tools_used: List of tools used
        execution_time: Total execution time in seconds
    """
    tools_str = ", ".join(tools_used) if tools_used else "none"
    
    logger.info(
        f"BI Interaction - Session: {session_id[:8]}... | "
        f"Input: {len(user_message)} chars | "
        f"Output: {len(ai_response)} chars | "
        f"Tools: [{tools_str}] | "
        f"Time: {execution_time:.2f}s" if execution_time else "Time: N/A"
    )


def log_tool_execution(
    logger: logging.Logger,
    tool_name: str,
    input_params: str,
    execution_time: float,
    success: bool = True,
    error: str = None
):
    """
    Log tool execution details.
    
    Args:
        logger: Logger instance
        tool_name: Name of the executed tool
        input_params: Input parameters
        execution_time: Execution time in seconds
        success: Whether execution was successful
        error: Error message if failed
    """
    status = "SUCCESS" if success else "FAILED"
    error_msg = f" | Error: {error}" if error else ""
    
    logger.info(
        f"Tool Execution - {tool_name} | "
        f"Status: {status} | "
        f"Input: {input_params[:50]}{'...' if len(input_params) > 50 else ''} | "
        f"Time: {execution_time:.2f}s{error_msg}"
    )


def log_api_request(
    logger: logging.Logger,
    endpoint: str,
    method: str,
    user_id: str = None,
    status_code: int = None,
    response_time: float = None
):
    """
    Log API request details.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint
        method: HTTP method
        user_id: User identifier
        status_code: HTTP status code
        response_time: Response time in seconds
    """
    user_str = f"User: {user_id} | " if user_id else ""
    status_str = f"Status: {status_code} | " if status_code else ""
    time_str = f"Time: {response_time:.3f}s" if response_time else ""
    
    logger.info(
        f"API Request - {method} {endpoint} | "
        f"{user_str}{status_str}{time_str}"
    )


# Global logger instances for common use
main_logger = get_logger("M32.Main")
agent_logger = get_logger("M32.Agent")
api_logger = get_logger("M32.API")
tool_logger = get_logger("M32.Tools")
