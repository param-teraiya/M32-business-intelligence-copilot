"""
Business Intelligence Agent for M32 System
Production-ready agent with comprehensive business intelligence capabilities.
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from base_agent import BaseAgent, AgentConfig, AgentMessage
from services.groq_service import GroqService
from services.tool_service import ToolService
from utils.logger import get_logger

logger = get_logger(__name__)


class BusinessIntelligenceAgent(BaseAgent):
    """
    Advanced Business Intelligence Agent with comprehensive analysis capabilities.
    Provides market research, competitor analysis, and strategic planning support.
    """
    
    def __init__(self):
        """Initialize the Business Intelligence Agent."""
        config = AgentConfig(
            name="BusinessIntelligenceAgent",
            description="Advanced business intelligence and strategic analysis",
            max_context_length=4000,
            temperature=0.7,
            max_tokens=1024,
            tools_enabled=[
                "web_search_business",
                "market_research", 
                "competitor_analysis",
                "business_strategy",
                "competitive_landscape",
                "business_model_analysis"
            ]
        )
        super().__init__(config)
        
        # Initialize services
        self.groq_service = GroqService()
        self.tool_service = ToolService()
        
        # System prompt for business intelligence
        self.system_prompt = """You are an expert Business Intelligence Copilot designed to help business owners and executives make data-driven strategic decisions.

Your expertise includes:
- Market research and industry analysis
- Competitive intelligence and benchmarking
- Business strategy development
- Business model optimization
- Financial analysis and planning
- Growth strategy formulation

Available tools:
- web_search_business(query): Search for current business information and news
- market_research(industry|region): Comprehensive market analysis and trends
- competitor_analysis(company|industry): Detailed competitor intelligence
- business_strategy(model|industry|size): Strategic planning and recommendations
- competitive_landscape(industry|size): Industry competitive analysis
- business_model_analysis(company|industry): Business model canvas and optimization

Guidelines:
1. Always provide actionable insights backed by data
2. Use appropriate business frameworks (Porter's Five Forces, SWOT, Business Model Canvas)
3. Tailor recommendations to company size and industry
4. Include specific metrics and KPIs when relevant
5. Consider both short-term tactics and long-term strategy
6. Use tools to gather current market data and insights

When using tools, format calls as: TOOL_USE: tool_name("parameters")

Provide responses in professional markdown format with clear structure, headings, and bullet points."""
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        business_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process business intelligence message."""
        
        try:
            print(f"Processing BI message for session {session_id}")
            if not self.validate_input(message):
                return self.format_error_response("Invalid input message", session_id)
            
            context = self.get_or_create_context(session_id, business_context)
            
            # Add user message to context
            user_message = AgentMessage(role="user", content=message)
            self.add_message_to_context(session_id, user_message)
            
            # Prepare conversation for LLM
            conversation_messages = self._prepare_conversation(context)
            
            # Get initial response from LLM
            llm_response = await self.groq_service.chat_completion(
                messages=conversation_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            if llm_response["status"] != "success":
                return self.format_error_response(
                    f"LLM error: {llm_response.get('error', 'Unknown error')}",
                    session_id
                )
            
            ai_response = llm_response["content"]
            tools_used = []
            
            # Process tool calls
            tool_pattern = r'TOOL_USE:\s*(\w+)\("([^"]+)"\)'
            tool_matches = re.findall(tool_pattern, ai_response)
            
            for tool_name, tool_input in tool_matches:
                if tool_name in self.config.tools_enabled:
                    try:
                        # Execute tool
                        tool_result = await self.tool_service.execute_tool(tool_name, tool_input)
                        tools_used.append(tool_name)
                        
                        # Update conversation with tool result
                        tool_message = AgentMessage(
                            role="system",
                            content=f"Tool {tool_name} result: {tool_result}",
                            metadata={"tool_name": tool_name, "tool_input": tool_input}
                        )
                        conversation_messages.append({
                            "role": "system",
                            "content": tool_message.content
                        })
                        
                    except Exception as e:
                        logger.error(f"Tool execution error for {tool_name}: {str(e)}")
                        # Continue with other tools
            
            # Get final response if tools were used
            if tools_used:
                # Add instruction for final response
                conversation_messages.append({
                    "role": "user",
                    "content": "Based on the tool results above, provide a comprehensive business intelligence analysis and actionable recommendations. Format your response in clear markdown with headings, bullet points, and structured insights."
                })
                
                final_response = await self.groq_service.chat_completion(
                    messages=conversation_messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                if final_response["status"] == "success":
                    ai_response = final_response["content"]
            
            # Clean up tool calls from final response
            ai_response = re.sub(r'TOOL_USE:\s*\w+\("[^"]+"\)\s*', '', ai_response).strip()
            
            # Add assistant response to context
            assistant_message = AgentMessage(
                role="assistant",
                content=ai_response,
                metadata={"tools_used": tools_used}
            )
            self.add_message_to_context(session_id, assistant_message)
            
            # Log interaction
            self.log_interaction(session_id, message, ai_response, tools_used)
            
            return self.format_success_response(
                response=ai_response,
                session_id=session_id,
                tools_used=tools_used,
                metadata={
                    "context_length": len(context.messages),
                    "business_context": context.business_context
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return self.format_error_response(str(e), session_id)
    
    def _prepare_conversation(self, context: AgentContext) -> List[Dict[str, str]]:
        """Prepare conversation messages for LLM."""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add business context if available
        if context.business_context:
            context_str = self._format_business_context(context.business_context)
            messages.append({
                "role": "system",
                "content": f"Business Context: {context_str}"
            })
        
        # Add recent conversation history
        recent_messages = context.get_recent_messages(limit=10)
        for msg in recent_messages:
            if msg.role in ["user", "assistant"]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return messages
    
    def _format_business_context(self, business_context: Dict[str, Any]) -> str:
        """Format business context for LLM."""
        context_parts = []
        
        if business_context.get("company"):
            context_parts.append(f"Company: {business_context['company']}")
        if business_context.get("industry"):
            context_parts.append(f"Industry: {business_context['industry']}")
        if business_context.get("business_type"):
            context_parts.append(f"Business Type: {business_context['business_type']}")
        if business_context.get("company_size"):
            context_parts.append(f"Company Size: {business_context['company_size']}")
        
        return " | ".join(context_parts)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return self.config.tools_enabled
    
    async def analyze_business_scenario(
        self,
        scenario: str,
        context: Dict[str, Any],
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Specialized method for analyzing business scenarios.
        
        Args:
            scenario: Business scenario description
            context: Business context information
            analysis_type: Type of analysis (comprehensive, competitive, strategic)
        """
        
        analysis_prompts = {
            "comprehensive": f"Provide a comprehensive business analysis of this scenario: {scenario}",
            "competitive": f"Focus on competitive analysis for this scenario: {scenario}",
            "strategic": f"Provide strategic recommendations for this scenario: {scenario}"
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["comprehensive"])
        
        return await self.process_message(
            message=prompt,
            session_id=f"analysis_{datetime.now().timestamp()}",
            business_context=context
        )
    
    async def generate_market_report(
        self,
        industry: str,
        region: str = "global",
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """Generate market report."""
        
        focus_areas = focus_areas or ["trends", "competition", "opportunities"]
        focus_str = ", ".join(focus_areas)
        
        prompt = f"Generate a comprehensive market report for the {industry} industry in {region}. Focus on: {focus_str}. Include market size, growth trends, key players, opportunities, and strategic recommendations."
        
        return await self.process_message(
            message=prompt,
            session_id=f"market_report_{datetime.now().timestamp()}",
            business_context={"industry": industry, "region": region}
        )
    
    async def competitive_intelligence_report(
        self,
        company: str,
        competitors: List[str],
        industry: str
    ) -> Dict[str, Any]:
        """Generate competitive intelligence report."""
        
        competitors_str = ", ".join(competitors)
        prompt = f"Create a competitive intelligence report for {company} against competitors: {competitors_str} in the {industry} industry. Include SWOT analysis, competitive positioning, and strategic recommendations."
        
        return await self.process_message(
            message=prompt,
            session_id=f"competitive_intel_{datetime.now().timestamp()}",
            business_context={
                "company": company,
                "industry": industry,
                "competitors": competitors
            }
        )


# Factory function for creating agent instances
def create_business_intelligence_agent() -> BusinessIntelligenceAgent:
    """Create and configure a new Business Intelligence Agent."""
    return BusinessIntelligenceAgent()
