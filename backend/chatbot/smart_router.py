import logging
from typing import List, Dict, Any, Optional
from .schemas import (
    RoutingDecision, RouteType, IntentResult, ConversationContext,
    RAGResult, SearchResult, ToolResponse
)
from .config import config
from datetime import datetime

logger = logging.getLogger(__name__)

class SemanticSmartRouter:
    """Routes queries based on semantic understanding and confidence scores"""
    
    def __init__(self, rag_system, external_search, tool_integrator, base_llm, calculator_selector, quick_calculator):
        self.rag_system = rag_system
        self.external_search = external_search
        self.tool_integrator = tool_integrator
        self.base_llm = base_llm
        self.calculator_selector = calculator_selector
        self.quick_calculator = quick_calculator
    
    async def route_query_semantically(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Make routing decisions based on semantic understanding"""
        
        try:
            logger.info(f"Routing query with intent: {intent.intent}, confidence: {intent.confidence}")
            
            # Check if calculator is needed
            if intent.calculator_type:
                return await self._route_to_calculator(intent, context)
            
            # Check if it's a knowledge-seeking query
            elif intent.intent.value in ["life_insurance_education", "product_comparison", "scenario_analysis"]:
                return await self._route_to_knowledge_sources(intent, context)
            
            # Check if it's client assessment support
            elif intent.intent.value == "client_assessment_support":
                return await self._route_to_client_assessment(intent, context)
            
            # Check if it's portfolio integration analysis
            elif intent.intent.value == "portfolio_integration_analysis":
                return await self._route_to_portfolio_analysis(intent, context)
            
            # Default fallback
            else:
                return await self._route_to_fallback(intent, context)
                
        except Exception as e:
            logger.error(f"Error in smart routing: {e}")
            return self._get_error_routing_decision(intent, context)
    
    async def _route_to_calculator(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to appropriate calculator based on semantic analysis"""
        
        try:
            # Use calculator selector to determine the best calculator
            calculator_selection = await self.calculator_selector.select_calculator_semantically(
                intent.semantic_goal, context
            )
            
            if calculator_selection.selected_calculator.value == "quick":
                return RoutingDecision(
                    route_type=RouteType.QUICK_CALCULATOR,
                    confidence=calculator_selection.confidence,
                    reasoning=calculator_selection.semantic_reasoning,
                    tool_type="quick_calculator",
                    session_id=context.session_id,
                    metadata={
                        "calculator_type": "quick",
                        "clarification_questions": calculator_selection.clarification_questions,
                        "expected_outcome": calculator_selection.expected_outcome
                    }
                )
            
            elif calculator_selection.selected_calculator.value in ["detailed", "portfolio"]:
                return RoutingDecision(
                    route_type=RouteType.EXTERNAL_TOOL,
                    confidence=calculator_selection.confidence,
                    reasoning=calculator_selection.semantic_reasoning,
                    tool_type=calculator_selection.selected_calculator.value,
                    session_id=context.session_id,
                    metadata={
                        "calculator_type": calculator_selection.selected_calculator.value,
                        "clarification_questions": calculator_selection.clarification_questions,
                        "expected_outcome": calculator_selection.expected_outcome
                    }
                )
            
            else:
                # Fallback to quick calculator
                return RoutingDecision(
                    route_type=RouteType.QUICK_CALCULATOR,
                    confidence=0.7,
                    reasoning="Fallback to quick calculator for calculation request",
                    tool_type="quick_calculator",
                    session_id=context.session_id,
                    metadata={
                        "calculator_type": "quick",
                        "clarification_questions": ["What is your age?", "What is your annual income?"],
                        "expected_outcome": "Immediate insurance needs estimate"
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in calculator routing: {e}")
            # Fallback to quick calculator
            return RoutingDecision(
                route_type=RouteType.QUICK_CALCULATOR,
                confidence=0.6,
                reasoning="Fallback to quick calculator due to routing error",
                tool_type="quick_calculator",
                session_id=context.session_id,
                metadata={
                    "calculator_type": "quick",
                    "clarification_questions": ["What is your age?", "What is your annual income?"],
                    "expected_outcome": "Immediate insurance needs estimate"
                }
            )
    
    async def _route_to_knowledge_sources(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to RAG, external search, or fallback based on confidence"""
        
        logger.info(f"Routing knowledge query: {intent.semantic_goal}")
        
        # Try RAG first
        try:
            rag_result = await self.rag_system.get_semantic_response(intent.semantic_goal, context)
            
            if rag_result.quality_score >= config.min_rag_confidence:
                return RoutingDecision(
                    route_type=RouteType.RAG,
                    confidence=rag_result.quality_score,
                    reasoning=f"High-quality RAG response available (score: {rag_result.quality_score:.2f})",
                    session_id=context.session_id,
                    metadata={
                        "rag_quality_score": rag_result.quality_score,
                        "source_documents": len(rag_result.source_documents),
                        "semantic_queries": rag_result.semantic_queries
                    }
                )
            
            logger.info(f"RAG quality below threshold: {rag_result.quality_score} < {config.min_rag_confidence}")
            
        except Exception as e:
            logger.error(f"Error in RAG routing: {e}")
            rag_result = None
        
        # Try external search if RAG failed or was low quality
        try:
            search_result = await self.external_search.search_with_evaluation(intent.semantic_goal, context)
            
            if search_result.quality_score >= config.min_search_confidence:
                return RoutingDecision(
                    route_type=RouteType.EXTERNAL_SEARCH,
                    confidence=search_result.quality_score,
                    reasoning=f"External search provided quality results (score: {search_result.quality_score:.2f})",
                    session_id=context.session_id,
                    metadata={
                        "search_quality_score": search_result.quality_score,
                        "source_results": len(search_result.source_results),
                        "original_query": search_result.original_query
                    }
                )
            
            logger.info(f"External search quality below threshold: {search_result.quality_score} < {config.min_search_confidence}")
            
        except Exception as e:
            logger.error(f"Error in external search routing: {e}")
            search_result = None
        
        # Fallback to base LLM
        return await self._route_to_fallback(intent, context)
    
    async def _route_to_client_assessment(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to external detailed client assessment tool"""
        
        try:
            tool_response = await self.tool_integrator.route_to_external_tool("detailed_assessment", context)
            
            return RoutingDecision(
                route_type=RouteType.EXTERNAL_TOOL,
                confidence=intent.confidence,
                reasoning="Comprehensive client assessment requires detailed external tool",
                tool_type="detailed_assessment",
                session_id=context.session_id,
                metadata={
                    "tool_url": tool_response.url,
                    "tool_message": tool_response.message,
                    "action": tool_response.action
                }
            )
            
        except Exception as e:
            logger.error(f"Error routing to client assessment: {e}")
            return self._get_error_routing_decision(intent, context)
    
    async def _route_to_portfolio_analysis(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to external portfolio analysis tool"""
        
        try:
            tool_response = await self.tool_integrator.route_to_external_tool("portfolio_analysis", context)
            
            return RoutingDecision(
                route_type=RouteType.EXTERNAL_TOOL,
                confidence=intent.confidence,
                reasoning="Portfolio-focused analysis requires specialized external tool",
                tool_type="portfolio_analysis",
                session_id=context.session_id,
                metadata={
                    "tool_url": tool_response.url,
                    "tool_message": tool_response.message,
                    "action": tool_response.action
                }
            )
            
        except Exception as e:
            logger.error(f"Error routing to portfolio analysis: {e}")
            return self._get_error_routing_decision(intent, context)
    
    async def _route_to_fallback(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to base LLM fallback"""
        
        return RoutingDecision(
            route_type=RouteType.BASE_LLM,
            confidence=0.5,
            reasoning="Using base LLM for general knowledge and fallback responses",
            session_id=context.session_id,
            metadata={
                "fallback_reason": "RAG and external search unavailable or low quality",
                "intent_confidence": intent.confidence
            }
        )
    
    def _get_error_routing_decision(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Get routing decision for error cases"""
        
        return RoutingDecision(
            route_type=RouteType.BASE_LLM,
            confidence=0.3,
            reasoning="Error in routing system, using base LLM fallback",
            session_id=context.session_id,
            metadata={
                "error": "Routing system error",
                "fallback": True
            }
        )

class ToolIntegrator:
    """Handles integration with external tools and calculators"""
    
    def __init__(self):
        self.tool_urls = {
            "detailed_assessment": "/assessment",
            "portfolio_analysis": "/portfolio-assessment",
            "quick_calculator": "/quick-calculator"
        }
        
        self.tool_descriptions = {
            "detailed_assessment": {
                "name": "New Client Detailed Assessment",
                "description": "Comprehensive 50+ question assessment for thorough financial planning",
                "estimated_time": "15-20 minutes",
                "output": "Detailed report with multiple scenarios and recommendations"
            },
            "portfolio_analysis": {
                "name": "Portfolio Analysis Calculator",
                "description": "Portfolio-focused insurance analysis with investment context",
                "estimated_time": "10-15 minutes",
                "output": "Portfolio analysis report with insurance integration"
            },
            "quick_calculator": {
                "name": "Quick Insurance Calculator",
                "description": "Fast 5-question estimate for immediate planning needs",
                "estimated_time": "2-3 minutes",
                "output": "Immediate coverage estimate with basic recommendations"
            }
        }
    
    async def route_to_external_tool(self, tool_type: str, context: ConversationContext) -> ToolResponse:
        """Route user to external tool with context preservation"""
        
        try:
            if tool_type not in self.tool_urls:
                raise ValueError(f"Unknown tool type: {tool_type}")
            
            tool_info = self.tool_descriptions[tool_type]
            
            # Generate deep link with session context
            deep_link = self._generate_deep_link(tool_type, context)
            
            # Create routing message
            message = self._generate_tool_routing_message(tool_type, context, tool_info)
            
            return ToolResponse(
                tool_type=tool_type,
                action="redirect_to_external_tool",
                url=deep_link,
                message=message,
                session_id=context.session_id
            )
            
        except Exception as e:
            logger.error(f"Error routing to external tool {tool_type}: {e}")
            raise
    
    def _generate_deep_link(self, tool_type: str, context: ConversationContext) -> str:
        """Generate deep link to external tool with context"""
        
        try:
            base_url = self.tool_urls[tool_type]
            
            # Add context parameters
            context_params = {
                "session_id": context.session_id,
                "knowledge_level": context.knowledge_level.value,
                "source": "robo_advisor_chatbot",
                "timestamp": context.created_at.isoformat()
            }
            
            # Build query string
            query_parts = [f"{k}={v}" for k, v in context_params.items()]
            query_string = "&".join(query_parts)
            
            deep_link = f"{base_url}?{query_string}"
            
            return deep_link
            
        except Exception as e:
            logger.error(f"Error generating deep link: {e}")
            return self.tool_urls.get(tool_type, "/")
    
    def _generate_tool_routing_message(
        self, 
        tool_type: str, 
        context: ConversationContext, 
        tool_info: Dict[str, Any]
    ) -> str:
        """Generate message explaining tool routing"""
        
        try:
            if tool_type == "detailed_assessment":
                return f"""
                **Redirecting to {tool_info['name']}**
                
                This comprehensive assessment will ask you 50+ detailed questions about your financial situation, goals, and needs. It typically takes {tool_info['estimated_time']} to complete.
                
                **What you'll get:**
                • {tool_info['output']}
                • Personalized recommendations
                • Multiple coverage scenarios
                • Detailed financial planning insights
                
                **After completion:**
                Your report will be sent back to this chat where you can ask questions and get additional guidance.
                
                [Click here to start the assessment]({self.tool_urls[tool_type]})
                """
            
            elif tool_type == "portfolio_analysis":
                return f"""
                **Redirecting to {tool_info['name']}**
                
                This specialized tool analyzes your insurance needs in the context of your investment portfolio. It typically takes {tool_info['estimated_time']} to complete.
                
                **What you'll get:**
                • {tool_info['output']}
                • Portfolio-insurance integration analysis
                • Risk management recommendations
                • Holistic financial planning insights
                
                **After completion:**
                Your portfolio analysis report will be sent back to this chat for further discussion and Q&A.
                
                [Click here to start the analysis]({self.tool_urls[tool_type]})
                """
            
            else:
                return f"""
                **Redirecting to {tool_info['name']}**
                
                This tool will help you {tool_info['description'].lower()}. It typically takes {tool_info['estimated_time']} to complete.
                
                **What you'll get:**
                • {tool_info['output']}
                
                [Click here to start]({self.tool_urls[tool_type]})
                """
                
        except Exception as e:
            logger.error(f"Error generating tool routing message: {e}")
            return f"Redirecting to {tool_type} tool..."
    
    async def handle_report_return(self, session_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report return from external tools"""
        
        try:
            # Process returned report data
            processed_report = {
                "session_id": session_id,
                "tool_type": report_data.get("tool_type", "unknown"),
                "report_id": report_data.get("report_id", ""),
                "generated_at": report_data.get("generated_at", ""),
                "summary": report_data.get("summary", ""),
                "key_findings": report_data.get("key_findings", []),
                "recommendations": report_data.get("recommendations", []),
                "download_url": report_data.get("download_url", ""),
                "metadata": report_data.get("metadata", {})
            }
            
            # Store report for chat context (in production, use database)
            if not hasattr(self, '_returned_reports'):
                self._returned_reports = {}
            
            self._returned_reports[session_id] = processed_report
            
            logger.info(f"Processed returned report for session {session_id}")
            
            return {
                "status": "success",
                "message": "Report successfully integrated into chat context",
                "report_summary": processed_report["summary"],
                "next_steps": [
                    "Ask questions about your report",
                    "Request clarification on recommendations",
                    "Discuss implementation strategies",
                    "Explore additional planning options"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error handling report return: {e}")
            return {
                "status": "error",
                "message": f"Error processing returned report: {str(e)}"
            }
    
    def get_returned_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get returned report for a session"""
        
        try:
            if hasattr(self, '_returned_reports') and session_id in self._returned_reports:
                return self._returned_reports[session_id]
            return None
            
        except Exception as e:
            logger.error(f"Error getting returned report: {e}")
            return None
    
    def cleanup_returned_reports(self, max_age_hours: int = 24) -> int:
        """Clean up old returned reports"""
        
        try:
            cleaned_count = 0
            current_time = datetime.utcnow()
            
            if hasattr(self, '_returned_reports'):
                session_ids_to_remove = []
                
                for session_id, report in self._returned_reports.items():
                    if "generated_at" in report:
                        try:
                            generated_time = datetime.fromisoformat(report["generated_at"])
                            age_hours = (current_time - generated_time).total_seconds() / 3600
                            
                            if age_hours > max_age_hours:
                                session_ids_to_remove.append(session_id)
                        except ValueError:
                            # Invalid timestamp, remove report
                            session_ids_to_remove.append(session_id)
                
                for session_id in session_ids_to_remove:
                    del self._returned_reports[session_id]
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old returned reports")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up returned reports: {e}")
            return 0 