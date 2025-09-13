from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import json
import re
from datetime import datetime

try:
    from .groq_client import groq_client, ChatMessage
except ImportError:
    from groq_client import groq_client, ChatMessage

try:
    from ..tools.web_search import web_search_tool
    from ..tools.market_research import market_research_tool
    from ..tools.competitor_analysis import competitor_analysis_tool
    from ..tools.business_strategy import business_strategy_tool
except ImportError:
    from web_search import web_search_tool
    from market_research import market_research_tool
    from competitor_analysis import competitor_analysis_tool
    from business_strategy import business_strategy_tool
try:
    from .config import get_groq_api_key, get_model_name
except ImportError:
    from config import get_groq_api_key, get_model_name


class ConversationContext(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    business_context: Dict[str, Any] = {}
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class BusinessIntelligenceAgent:
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
        print("Initializing BI agent...")
        
        self.available_tools = {
            "web_search_business": self._web_search_wrapper,
            "competitor_analysis": self._competitor_analysis_wrapper,
            "market_trends": self._market_trends_wrapper,
            "industry_insights": self._industry_insights_wrapper,
            "market_research": self._market_research_wrapper,
            "business_strategy": self._business_strategy_wrapper,
            "competitive_landscape": self._competitive_landscape_wrapper,
            "business_model_analysis": self._business_model_wrapper
        }
        
        self.system_prompt = """You are a Business Intelligence assistant for small and medium business owners.

Available tools (use this exact format):
- TOOL_USE: web_search_business("search query")
- TOOL_USE: competitor_analysis("company|industry")
- TOOL_USE: market_trends("industry")
- TOOL_USE: industry_insights("industry|topic")

Keep responses practical and actionable. Use tools when you need current data."""

    def chat(
        self, 
        message: str, 
        session_id: str = "default",
        business_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            if session_id not in self.contexts:
                self.contexts[session_id] = ConversationContext(session_id=session_id)
                print(f"Created new session: {session_id}")
            
            context = self.contexts[session_id]
            
            if business_context:
                context.business_context.update(business_context)
            
            user_message = ChatMessage(role="user", content=message)
            context.messages.append(user_message)
            
            conversation_messages = []
            conversation_messages.append(ChatMessage(role="system", content=self.system_prompt))
            
            recent_messages = context.messages[-8:]
            conversation_messages.extend(recent_messages)
            
            response_result = groq_client.create_chat_completion(
                messages=conversation_messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            if response_result["status"] != "success":
                return {
                    "status": "error",
                    "error": f"AI response failed: {response_result['error']}",
                    "session_id": session_id
                }
            
            ai_response = response_result["content"]
            tools_used = []
            
            tool_matches = re.findall(r'TOOL_USE:\s*(\w+)\("([^"]+)"\)', ai_response)
            
            if tool_matches:
                print(f"Found {len(tool_matches)} tool calls")
                for tool_name, tool_params in tool_matches:
                    if tool_name in self.available_tools:
                        tools_used.append(tool_name)
                        tool_result = self.available_tools[tool_name](tool_params)
                        
                        tool_message = ChatMessage(
                            role="system", 
                            content=f"Tool '{tool_name}' results: {tool_result}"
                        )
                        conversation_messages.append(tool_message)
                
                if tools_used:
                    final_response_result = groq_client.create_chat_completion(
                        messages=conversation_messages,
                        temperature=0.7,
                        max_tokens=1024
                    )
                    
                    if final_response_result["status"] == "success":
                        ai_response = final_response_result["content"]
            
            ai_response = re.sub(r'TOOL_USE:\s*\w+\("[^"]+"\)\s*', '', ai_response)
            ai_response = ai_response.strip()
            
            assistant_message = ChatMessage(role="assistant", content=ai_response)
            context.messages.append(assistant_message)
            context.updated_at = datetime.now()
            
            return {
                "status": "success",
                "response": ai_response,
                "session_id": session_id,
                "context_length": len(context.messages),
                "tools_used": tools_used
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    def get_conversation_history(self, session_id: str) -> List[ChatMessage]:
        """Get conversation history for a session."""
        if session_id in self.contexts:
            return self.contexts[session_id].messages
        return []
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session."""
        if session_id in self.contexts:
            del self.contexts[session_id]
            return True
        return False
    
    def _web_search_wrapper(self, query: str) -> str:
        """Wrapper for web search tool."""
        result = web_search_tool.search_business_info(query, max_results=5)
        
        if result["status"] == "success":
            formatted_results = []
            for search_result in result["results"][:3]:  # Top 3 results
                formatted_results.append(
                    f"**{search_result.title}**\n"
                    f"Source: {search_result.url}\n"
                    f"Summary: {search_result.snippet[:200]}...\n"
                )
            return "\n".join(formatted_results)
        else:
            return f"Search failed: {result['error']}"
    
    def _competitor_analysis_wrapper(self, input_str: str) -> str:
        """Wrapper for competitor analysis tool."""
        try:
            # Parse input (expecting "company_name|industry" format)
            parts = input_str.split("|")
            if len(parts) >= 2:
                company_name, industry = parts[0].strip(), parts[1].strip()
            else:
                return "Please provide input in format: 'Company Name|Industry'"
            
            result = web_search_tool.search_competitors(company_name, industry)
            
            if result["status"] == "success":
                formatted_results = []
                for search_result in result["results"][:3]:
                    formatted_results.append(
                        f"**{search_result.title}**\n"
                        f"Relevance: {search_result.relevance_score or 'N/A'}\n"
                        f"Summary: {search_result.snippet[:200]}...\n"
                    )
                return f"Competitor analysis for {company_name} in {industry}:\n\n" + "\n".join(formatted_results)
            else:
                return f"Competitor analysis failed: {result['error']}"
                
        except Exception as e:
            return f"Error in competitor analysis: {str(e)}"
    
    def _market_trends_wrapper(self, industry: str) -> str:
        """Wrapper for market trends tool."""
        result = web_search_tool.search_market_trends(industry)
        
        if result["status"] == "success":
            formatted_results = []
            for search_result in result["results"][:3]:
                formatted_results.append(
                    f"**{search_result.title}**\n"
                    f"Summary: {search_result.snippet[:200]}...\n"
                )
            return f"Market trends for {industry}:\n\n" + "\n".join(formatted_results)
        else:
            return f"Market trends search failed: {result['error']}"
    
    def _industry_insights_wrapper(self, input_str: str) -> str:
        """Wrapper for industry insights tool."""
        try:
            # Parse input (expecting "industry|topic" format)
            parts = input_str.split("|")
            if len(parts) >= 2:
                industry, topic = parts[0].strip(), parts[1].strip()
            else:
                return "Please provide input in format: 'Industry|Topic'"
            
            result = web_search_tool.search_industry_insights(industry, topic)
            
            if result["status"] == "success":
                formatted_results = []
                for search_result in result["results"][:3]:
                    formatted_results.append(
                        f"**{search_result.title}**\n"
                        f"Summary: {search_result.snippet[:200]}...\n"
                    )
                return f"Industry insights for {topic} in {industry}:\n\n" + "\n".join(formatted_results)
            else:
                return f"Industry insights search failed: {result['error']}"
                
        except Exception as e:
            return f"Error in industry insights: {str(e)}"
    
    async def _market_research_wrapper(self, input_str: str) -> str:
        """Wrapper for advanced market research tool."""
        try:
            # Parse input (expecting "industry|region" or just "industry")
            parts = input_str.split("|")
            industry = parts[0].strip()
            region = parts[1].strip() if len(parts) > 1 else "global"
            
            result = await market_research_tool.analyze_market_trends(industry, region)
            
            # Format the comprehensive market research results
            formatted_output = f"# Market Research: {industry}\n\n"
            formatted_output += f"**Market Size**: {result.get('market_size', 'N/A')}\n"
            formatted_output += f"**Growth Rate**: {result.get('growth_rate', 'N/A')}\n\n"
            
            if result.get('key_trends'):
                formatted_output += "## Key Market Trends:\n"
                for trend in result['key_trends']:
                    formatted_output += f"• {trend}\n"
                formatted_output += "\n"
            
            if result.get('opportunities'):
                formatted_output += "## Opportunities:\n"
                for opp in result['opportunities']:
                    formatted_output += f"• {opp}\n"
                formatted_output += "\n"
            
            if result.get('recommendations'):
                formatted_output += "## Strategic Recommendations:\n"
                for rec in result['recommendations']:
                    formatted_output += f"• {rec}\n"
            
            return formatted_output
            
        except Exception as e:
            return f"Market research analysis failed: {str(e)}"
    
    async def _business_strategy_wrapper(self, input_str: str) -> str:
        """Wrapper for business strategy tool."""
        try:
            # Parse input (expecting "current_model|industry|company_size")
            parts = input_str.split("|")
            if len(parts) >= 3:
                current_model, industry, company_size = parts[0].strip(), parts[1].strip(), parts[2].strip()
            else:
                return "Please provide input in format: 'Business Model|Industry|Company Size'"
            
            result = await business_strategy_tool.business_model_analysis(current_model, industry, company_size)
            
            formatted_output = f"# Business Strategy Analysis\n\n"
            formatted_output += f"**Current Model**: {result['model_analysis']['model_type']}\n"
            formatted_output += f"**Description**: {result['model_analysis']['description']}\n\n"
            
            formatted_output += "## Revenue Streams:\n"
            for stream in result['model_analysis']['revenue_streams']:
                formatted_output += f"• {stream}\n"
            formatted_output += "\n"
            
            formatted_output += "## Strategic Recommendations:\n"
            for rec in result['strategic_recommendations']:
                formatted_output += f"• {rec}\n"
            
            return formatted_output
            
        except Exception as e:
            return f"Business strategy analysis failed: {str(e)}"
    
    async def _competitive_landscape_wrapper(self, input_str: str) -> str:
        """Wrapper for competitive landscape analysis."""
        try:
            # Parse input (expecting "industry|company_size")
            parts = input_str.split("|")
            industry = parts[0].strip()
            company_size = parts[1].strip() if len(parts) > 1 else "medium"
            
            result = await competitor_analysis_tool.competitive_landscape_analysis(industry, company_size)
            
            formatted_output = f"# Competitive Landscape: {industry}\n\n"
            formatted_output += f"**Market Concentration**: {result['market_structure']['concentration']}\n"
            formatted_output += f"**Competitive Intensity**: {result['competitive_dynamics']['intensity']}\n\n"
            
            formatted_output += "## Market Leaders:\n"
            for leader in result['market_structure']['market_leaders']:
                formatted_output += f"• {leader}\n"
            formatted_output += "\n"
            
            formatted_output += "## Key Success Factors:\n"
            for factor in result['competitive_dynamics']['key_factors']:
                formatted_output += f"• {factor}\n"
            formatted_output += "\n"
            
            formatted_output += "## Opportunities for New Entrants:\n"
            for opp in result['opportunities_for_new_entrants']:
                formatted_output += f"• {opp}\n"
            
            return formatted_output
            
        except Exception as e:
            return f"Competitive landscape analysis failed: {str(e)}"
    
    async def _business_model_wrapper(self, input_str: str) -> str:
        """Wrapper for business model canvas analysis."""
        try:
            # Parse input (expecting "company_name|industry")
            parts = input_str.split("|")
            if len(parts) >= 2:
                company_name, industry = parts[0].strip(), parts[1].strip()
            else:
                return "Please provide input in format: 'Company Name|Industry'"
            
            result = await business_strategy_tool.business_model_canvas(company_name, industry)
            
            formatted_output = f"# Business Model Canvas: {company_name}\n\n"
            
            canvas = result['business_model_canvas']
            formatted_output += f"## Value Propositions\n"
            formatted_output += f"{canvas['value_propositions']['description']}\n\n"
            
            formatted_output += f"## Key Resources\n"
            for resource in canvas['key_resources']['examples']:
                formatted_output += f"• {resource}\n"
            formatted_output += "\n"
            
            formatted_output += f"## Revenue Streams\n"
            for stream in canvas['revenue_streams']['examples']:
                formatted_output += f"• {stream}\n"
            formatted_output += "\n"
            
            formatted_output += f"## Customer Segments\n"
            for segment in canvas['customer_segments']['examples']:
                formatted_output += f"• {segment}\n"
            
            return formatted_output
            
        except Exception as e:
            return f"Business model analysis failed: {str(e)}"


# Global agent instance
business_agent = BusinessIntelligenceAgent()


async def test_langchain_integration() -> None:
    """Test the Business Intelligence Agent with business scenarios."""
    print("Testing Business Intelligence Agent...")
    
    # Test basic chat
    print("\n1. Testing basic business query...")
    result = business_agent.chat(
        "What are the current trends in the SaaS industry?",
        session_id="test_session"
    )
    
    if result["status"] == "success":
        print("✅ Basic chat successful!")
        print(f"Response: {result['response'][:200]}...")
        print(f"Tools used: {result['tools_used']}")
    else:
        print(f"❌ Basic chat failed: {result['error']}")
    
    # Test follow-up with context
    print("\n2. Testing context management...")
    followup = business_agent.chat(
        "How does this affect small businesses specifically?",
        session_id="test_session"
    )
    
    if followup["status"] == "success":
        print("✅ Context management working!")
        print(f"Context length: {followup['context_length']} messages")
    else:
        print(f"❌ Context test failed: {followup['error']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_langchain_integration())