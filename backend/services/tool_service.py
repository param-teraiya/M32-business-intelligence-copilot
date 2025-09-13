"""
Tool Service for M32 Business Intelligence Copilot
"""

import sys
import os
from typing import Dict, Any, List

# Add tools directory to path
tools_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'tools')
if tools_path not in sys.path:
    sys.path.append(tools_path)


class ToolService:
    """Service for managing business intelligence tools."""
    
    def __init__(self):
        """Initialize the tool service."""
        self.available_tools = {}
        self._load_tools()
    
    def _load_tools(self):
        """Load available business intelligence tools."""
        try:
            # Try to import tools
            from web_search import web_search_tool
            from market_research import market_research_tool
            from competitor_analysis import competitor_analysis_tool
            from business_strategy import business_strategy_tool
            
            self.available_tools = {
                'web_search': web_search_tool,
                'market_research': market_research_tool,
                'competitor_analysis': competitor_analysis_tool,
                'business_strategy': business_strategy_tool
            }
            print(f"✅ Loaded {len(self.available_tools)} business intelligence tools")
            
        except ImportError as e:
            print(f"⚠️ Could not load tools: {e}")
            self.available_tools = {}
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self.available_tools.keys())
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a business intelligence tool."""
        if tool_name not in self.available_tools:
            return {
                "status": "error",
                "error": f"Tool '{tool_name}' not found",
                "available_tools": self.get_available_tools()
            }
        
        try:
            tool_function = self.available_tools[tool_name]
            result = tool_function(**kwargs)
            return {
                "status": "success",
                "result": result,
                "tool": tool_name
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Tool execution failed: {str(e)}",
                "tool": tool_name
            }


# Global instance
tool_service = ToolService()