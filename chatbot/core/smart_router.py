import logging
from typing import List, Dict, Any, Optional
from .schemas import (
    RoutingDecision, RouteType, IntentResult, ConversationContext,
    RAGResult, SearchResult, ToolResponse
)
from .config import config
from datetime import datetime
from .schemas import CalculatorType, IntentCategory

logger = logging.getLogger(__name__)

class SemanticSmartRouter:
    """Routes queries based on semantic understanding and confidence scores"""
    
    def __init__(self, external_search, tool_integrator, base_llm, calculator_selector, quick_calculator):
        self.external_search = external_search
        self.tool_integrator = tool_integrator
        self.base_llm = base_llm
        self.calculator_selector = calculator_selector
        self.quick_calculator = quick_calculator
    
    async def route_query_semantically(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Make routing decisions based on semantic understanding"""
        
        try:
            logger.info(f"🎯 SMART ROUTER: Starting semantic routing")
            logger.info(f"🎯 SMART ROUTER: Intent enum: {intent.intent}")
            logger.info(f"🎯 SMART ROUTER: Intent value: {intent.intent.value}")
            logger.info(f"🎯 SMART ROUTER: Confidence: {intent.confidence}")
            logger.info(f"🎯 SMART ROUTER: Reasoning: {intent.reasoning}")
            
            # NEW: Handle calculator selection choice
            if intent.intent == IntentCategory.CALCULATOR_SELECTION_CHOICE:
                logger.info("🎯 SMART ROUTER: Routing to calculator selection choice")
                return await self._route_to_calculator_selection(intent, context)
            
            # NEW: Handle calculator choice selection
            elif intent.intent == IntentCategory.CALCULATOR_CHOICE_SELECTED:
                logger.info("🎯 SMART ROUTER: Routing to selected calculator")
                return await self._route_to_selected_calculator(intent, context)
            
            # ONLY route to calculator if intent ACTUALLY requires calculation
            elif intent.intent in [IntentCategory.INSURANCE_NEEDS_CALCULATION, IntentCategory.PORTFOLIO_INTEGRATION_ANALYSIS]:
                logger.info("🎯 SMART ROUTER: Routing to calculator (enum check)")
                return await self._route_to_calculator(intent, context)
            
            # Check if it's a knowledge-seeking query
            elif intent.intent in [IntentCategory.LIFE_INSURANCE_EDUCATION, IntentCategory.PRODUCT_COMPARISON, IntentCategory.SCENARIO_ANALYSIS]:
                logger.info("🎯 SMART ROUTER: Routing to knowledge sources")
                return await self._route_to_knowledge_sources(intent, context)
            
            # Check if it's client assessment support
            elif intent.intent == IntentCategory.CLIENT_ASSESSMENT_SUPPORT:
                logger.info("🎯 SMART ROUTER: Routing to client assessment")
                return await self._route_to_client_assessment(intent, context)
            
            # Check if it's portfolio integration analysis
            elif intent.intent == IntentCategory.PORTFOLIO_INTEGRATION_ANALYSIS:
                logger.info("🎯 SMART ROUTER: Routing to portfolio analysis")
                return await self._route_to_portfolio_analysis(intent, context)
            
            # NEW: Handle conversation management queries
            elif intent.intent == IntentCategory.CONVERSATION_MANAGEMENT:
                logger.info("🎯 SMART ROUTER: Routing to conversation management")
                return await self._route_to_conversation_management(intent, context)
            
            # NEW: Handle report questions
            elif intent.intent == IntentCategory.REPORT_QUESTION:
                logger.info("🎯 SMART ROUTER: Routing to report question handler")
                return await self._route_to_report_question(intent, context)
            
            # NEW: Handle quick calculator follow-up questions
            elif intent.intent == IntentCategory.QUICK_CALCULATOR_FOLLOW_UP:
                logger.info("🎯 SMART ROUTER: Routing to quick calculator follow-up handler")
                return await self._route_to_quick_calculator_follow_up(intent, context)
            
            # NEW: Handle file analysis questions
            elif intent.intent == IntentCategory.FILE_ANALYSIS:
                logger.info("🎯 SMART ROUTER: Routing to file analysis")
                return await self._route_to_file_analysis(intent, context)
            
            # Default fallback - but check for conversation management keywords first
            else:
                logger.info(f"🎯 SMART ROUTER: Defaulting to fallback for intent: {intent.intent.value}")
                
                # LAST RESORT: Check if this might be conversation management despite intent classification
                query_lower = intent.semantic_goal.lower() if intent.semantic_goal else ""
                conversation_keywords = [
                    "what did we just talk about", "what were we discussing", "summarize our conversation",
                    "what have we covered", "what was the main topic", "repeat what you said",
                    "how long have we been talking", "what questions have I asked"
                ]
                
                if any(keyword in query_lower for keyword in conversation_keywords):
                    logger.info("🎯 SMART ROUTER: Detected conversation management keywords in fallback, routing to conversation management")
                    return await self._route_to_conversation_management(intent, context)
                
                return await self._route_to_fallback(intent, context)
                
        except Exception as e:
            logger.error(f"🎯 SMART ROUTER: Error in smart routing: {e}")
            import traceback
            logger.error(f"🎯 SMART ROUTER: Full traceback: {traceback.format_exc()}")
            return self._get_error_routing_decision(intent, context, f"Smart routing error: {str(e)}")
    
    async def _route_to_calculator(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to appropriate calculator based on intent"""
        
        try:
            # Check if this is a calculator-related query
            if intent.calculator_type == CalculatorType.QUICK:
                # Route to quick calculator
                return RoutingDecision(
                    route_type=RouteType.QUICK_CALCULATOR,
                    confidence=intent.confidence,
                    reasoning=f"User needs quick calculation: {intent.reasoning}",
                    tool_type=None,
                    session_id=context.session_id
                )
            
            elif intent.calculator_type == CalculatorType.DETAILED:
                # Route to detailed assessment tool
                return RoutingDecision(
                    route_type=RouteType.EXTERNAL_TOOL,
                    confidence=intent.confidence,
                    reasoning=f"User needs detailed assessment: {intent.reasoning}",
                    tool_type="assessment",
                    session_id=context.session_id
                )
            
            elif intent.calculator_type == CalculatorType.PORTFOLIO:
                # Route to portfolio analysis tool
                return RoutingDecision(
                    route_type=RouteType.EXTERNAL_TOOL,
                    confidence=intent.confidence,
                    reasoning=f"User needs portfolio analysis: {intent.reasoning}",
                    tool_type="portfolio",
                    session_id=context.session_id
                )
            
            else:
                # No calculator needed
                return RoutingDecision(
                    route_type=RouteType.RAG,
                    confidence=intent.confidence,
                    reasoning=f"No calculation needed: {intent.reasoning}",
                    tool_type=None,
                    session_id=context.session_id
                )
                
        except Exception as e:
            logger.error(f"Error routing to calculator: {e}")
            return RoutingDecision(
                route_type=RouteType.BASE_LLM,
                confidence=0.5,
                reasoning=f"Calculator routing error: {str(e)}",
                tool_type=None,
                session_id=context.session_id
            )
    
    async def _route_to_calculator_selection(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to calculator selection when user needs to choose calculator type"""
        try:
            # Set calculator state to selecting
            context.calculator_state = "selecting"
            
            return RoutingDecision(
                route_type=RouteType.CALCULATOR_SELECTION,
                confidence=intent.confidence,
                reasoning="User needs to choose calculator type",
                tool_type=None,
                session_id=context.session_id,
                metadata={
                    "needs_calculator_selection": True,
                    "suggested_calculator": intent.suggested_calculator or "quick"
                }
            )
            
        except Exception as e:
            logger.error(f"Error routing to calculator selection: {e}")
            return self._get_error_routing_decision(intent, context, f"Calculator selection routing failed: {str(e)}")
    
    async def _route_to_selected_calculator(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to the calculator type the user selected"""
        try:
            selected_calc = intent.calculator_type
            
            # Update context with selected calculator
            context.calculator_type = selected_calc
            context.calculator_state = "active"
            
            if selected_calc == CalculatorType.QUICK:
                # Start quick calculator session
                from datetime import datetime
                session_id = f"calc_{int(datetime.utcnow().timestamp())}"
                context.calculator_session = {"session_id": session_id, "type": "quick"}
                
                return RoutingDecision(
                    route_type=RouteType.QUICK_CALCULATOR,
                    confidence=1.0,
                    reasoning=f"User selected {selected_calc} calculator",
                    tool_type=None,
                    session_id=context.session_id,
                    metadata={"calculator_session_id": session_id}
                )
            
            elif selected_calc == CalculatorType.DETAILED:
                return await self._route_to_client_assessment(intent, context)
            
            elif selected_calc == CalculatorType.PORTFOLIO:
                return await self._route_to_portfolio_analysis(intent, context)
            
            else:
                # Fallback to RAG if calculator type is unclear
                return RoutingDecision(
                    route_type=RouteType.RAG,
                    confidence=0.5,
                    reasoning=f"Unclear calculator type: {selected_calc}",
                    tool_type=None,
                    session_id=context.session_id
                )
                
        except Exception as e:
            logger.error(f"Error routing to selected calculator: {e}")
            return self._get_error_routing_decision(intent, context, f"Selected calculator routing failed: {str(e)}")
    
    async def _route_to_knowledge_sources(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route knowledge queries to RAG system with optional external search"""
        try:
            logger.info(f"Routing knowledge query: {intent.intent.value}")
            
            # For calculator intents, NEVER use external search
            if intent.intent in [IntentCategory.INSURANCE_NEEDS_CALCULATION, 
                               IntentCategory.CLIENT_ASSESSMENT_SUPPORT, 
                               IntentCategory.PORTFOLIO_INTEGRATION_ANALYSIS]:
                logger.info("Calculator intent detected - bypassing external search")
                needs_search = False
            else:
                # Use the intent classifier's decision about external search
                needs_search = intent.needs_external_search
                logger.info(f"Intent classifier determined search need: {needs_search}")
            
            # Determine route type based on intent and context
            # Don't call RAG here - let the orchestrator handle RAG execution
            route_type = RouteType.RAG
            reasoning = f"Knowledge query routed to RAG system for comprehensive response"
            
            return RoutingDecision(
                route_type=route_type,
                confidence=intent.confidence,
                reasoning=reasoning,
                session_id=context.session_id,
                metadata={
                    "needs_external_search": needs_search,  # Pass through the search decision
                    "intent_confidence": intent.confidence,
                    "semantic_goal": intent.semantic_goal
                }
            )
            
        except Exception as e:
            logger.error(f"Error routing to knowledge sources: {e}")
            return self._get_error_routing_decision(intent, context, f"Knowledge routing failed: {str(e)}")
    
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
            return self._get_error_routing_decision(intent, context, f"Client assessment routing failed: {str(e)}")
    
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
            return self._get_error_routing_decision(intent, context, f"Portfolio analysis routing failed: {str(e)}")
    
    async def _route_to_conversation_management(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route conversation management queries to the memory system"""
        try:
            logger.info("🎯 SMART ROUTER: Creating conversation management routing decision")
            
            return RoutingDecision(
                route_type=RouteType.CONVERSATION_MANAGEMENT,
                confidence=intent.confidence,
                reasoning=f"User is asking about conversation state: {intent.reasoning}",
                tool_type=None,
                session_id=context.session_id
            )
            
        except Exception as e:
            logger.error(f"🎯 SMART ROUTER: Error routing to conversation management: {e}")
            import traceback
            logger.error(f"🎯 SMART ROUTER: Full traceback: {traceback.format_exc()}")
            return self._get_error_routing_decision(intent, context, f"Conversation management routing failed: {str(e)}")
    
    async def _route_to_report_question(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route report questions to the report context system"""
        try:
            logger.info("🎯 SMART ROUTER: Creating report question routing decision")
            
            return RoutingDecision(
                route_type=RouteType.BASE_LLM,  # Will be handled by orchestrator with report context
                confidence=intent.confidence,
                reasoning=f"User is asking about existing report: {intent.reasoning}",
                tool_type=None,
                session_id=context.session_id,
                metadata={
                    "report_question": True,
                    "requires_report_context": True
                }
            )
            
        except Exception as e:
            logger.error(f"🎯 SMART ROUTER: Error routing to report question: {e}")
            import traceback
            logger.error(f"🎯 SMART ROUTER: Full traceback: {traceback.format_exc()}")
    
    async def _route_to_quick_calculator_follow_up(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route quick calculator follow-up questions to BASE_LLM with calculator context"""
        try:
            logger.info("🎯 SMART ROUTER: Creating quick calculator follow-up routing decision")
            
            return RoutingDecision(
                route_type=RouteType.BASE_LLM,  # Will be handled by orchestrator with calculator context
                confidence=intent.confidence,
                reasoning=f"User is asking about quick calculator results: {intent.reasoning}",
                tool_type=None,
                session_id=context.session_id,
                metadata={
                    "quick_calculator_follow_up": True,
                    "requires_calculator_context": True
                }
            )
            
        except Exception as e:
            logger.error(f"🎯 SMART ROUTER: Error routing to quick calculator follow-up: {e}")
            import traceback
            logger.error(f"🎯 SMART ROUTER: Full traceback: {traceback.format_exc()}")
            return self._get_error_routing_decision(intent, context, f"Report question routing failed: {str(e)}")
    
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
    
    def _get_error_routing_decision(self, intent: IntentResult, context: ConversationContext, error_reason: str) -> RoutingDecision:
        """Get routing decision for error cases"""
        
        return RoutingDecision(
            route_type=RouteType.BASE_LLM,
            confidence=0.3,
            reasoning=f"Error in routing system, using base LLM fallback: {error_reason}",
            session_id=context.session_id,
            metadata={
                "error": "Routing system error",
                "fallback": True
            }
        )
    
    async def _route_to_file_analysis(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route file analysis questions"""
        
        try:
            logger.info("🎯 SMART ROUTER: Creating file analysis routing decision")
            
            # File analysis should use external tool (file processor)
            return RoutingDecision(
                route_type=RouteType.EXTERNAL_TOOL,
                confidence=intent.confidence,
                reasoning=f"File analysis question: {intent.reasoning}",
                metadata={
                    "is_file_analysis": True,
                    "tool_type": "file_processor",
                    "query": intent.semantic_goal
                }
            )
        except Exception as e:
            logger.error(f"🎯 SMART ROUTER: Error routing to file analysis: {e}")
            return self._get_error_routing_decision(intent, context, f"File analysis routing failed: {str(e)}")

class ToolIntegrator:
    """Handles integration with external tools and calculators"""
    
    def __init__(self, session_linker=None):
        self.session_linker = session_linker
        self.tool_urls = {
            "detailed_assessment": "/assessment",
            "client_assessment": "/assessment",  # Alias for client_assessment
            "portfolio_analysis": "/portfolio-assessment",
            "quick_calculator": "/quick-calculator",
            "assessment": "/assessment",  # New unified mapping
            "portfolio": "/portfolio-assessment"  # New unified mapping
        }
        
        self.tool_descriptions = {
            "detailed_assessment": {
                "name": "New Client Detailed Assessment",
                "description": "Comprehensive 50+ question assessment for thorough financial planning",
                "estimated_time": "15-20 minutes",
                "output": "Detailed report with multiple scenarios and recommendations"
            },
            "client_assessment": {
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
            },
            "assessment": {
                "name": "Client Assessment Tool",
                "description": "Comprehensive life insurance needs assessment",
                "estimated_time": "15-20 minutes",
                "output": "Detailed PDF report with recommendations",
                "icon": "📋"
            },
            "portfolio": {
                "name": "Portfolio Analysis Tool", 
                "description": "Complete portfolio analysis and recommendations",
                "estimated_time": "10-15 minutes",
                "output": "Portfolio analysis PDF report",
                "icon": "📊"
            }
        }
    
    async def route_to_external_tool(self, tool_type: str, context: ConversationContext) -> ToolResponse:
        """Route user to external tool with session linking"""
        
        try:
            if tool_type not in self.tool_urls:
                raise ValueError(f"Unknown tool type: {tool_type}")
            
            tool_info = self.tool_descriptions[tool_type]
            
            # Create tool session if session linker is available
            external_session_id = None
            if self.session_linker:
                try:
                    external_session_id = await self.session_linker.create_tool_session(
                        context.session_id, 
                        tool_type
                    )
                    logger.info(f"🔗 Created tool session: {external_session_id} for chat session: {context.session_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to create tool session: {e}")
                    print(f"Warning: Could not create tool session: {e}")
            else:
                logger.warning("⚠️ Session linker not available - using base session ID")
            
            # Generate deep link with session context
            deep_link = self._generate_deep_link(tool_type, context, external_session_id)
            
            # Create routing message
            message = self._generate_tool_routing_message(tool_type, context, tool_info, deep_link)
            
            return ToolResponse(
                tool_type=tool_type,
                action="redirect_to_external_tool",
                url=deep_link,
                message=message,
                session_id=external_session_id or context.session_id
            )
            
        except Exception as e:
            print(f"Error routing to external tool {tool_type}: {e}")
            # Return error response instead of raising
            return ToolResponse(
                tool_type=tool_type,
                action="error",
                message=f"Failed to open {tool_type} tool: {str(e)}",
                session_id=context.session_id
            )
    
    def _generate_deep_link(self, tool_type: str, context: ConversationContext, external_session_id: str = None) -> str:
        """Generate deep link to external tool with context"""
        
        try:
            base_url = self.tool_urls[tool_type]
            
            # Use external_session_id if available, otherwise fall back to context.session_id
            session_id_to_use = external_session_id or context.session_id
            
            # Add context parameters
            context_params = {
                "session_id": session_id_to_use,
                "knowledge_level": context.knowledge_level.value,
                "source": "robo_advisor_chatbot",
                "timestamp": context.created_at.isoformat()
            }
            
            # Build query string
            query_parts = [f"{k}={v}" for k, v in context_params.items()]
            query_string = "&".join(query_parts)
            
            deep_link = f"{base_url}?{query_string}"
            
            logger.info(f"🔗 Generated deep link: {deep_link}")
            logger.info(f"🔗 Using session ID: {session_id_to_use} (external: {external_session_id}, context: {context.session_id})")
            
            return deep_link
            
        except Exception as e:
            logger.error(f"Error generating deep link: {e}")
            return self.tool_urls.get(tool_type, "/")
    
    def _generate_tool_routing_message(
        self, 
        tool_type: str, 
        context: ConversationContext, 
        tool_info: Dict[str, Any],
        deep_link: str
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
                
                [Click here to start the assessment]({deep_link})
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
                
                [Click here to start the analysis]({deep_link})
                """
            
            elif tool_type in ["assessment", "portfolio"]:
                icon = tool_info.get('icon', '🔧')
                return f"""
                {icon} **Opening {tool_info['name']}**
                
                I'm opening a dedicated tool for this analysis. This form will open in a new tab and will take approximately {tool_info['estimated_time']}.
                
                **What happens next:**
                1. 📝 Complete the detailed assessment
                2. 📊 Your data will be analyzed  
                3. 📄 **You'll receive a downloadable PDF report**
                4. 🤖 **The report will appear here in our chat automatically**
                5. 💬 Ask me any follow-up questions about your results
                
                **Output:** {tool_info['output']}
                
                🔗 **The tool will open in a new tab** - please complete it there and return here for your results and any questions!
                
                **Fallback Link:** If the tool doesn't open automatically, [click here to open {tool_info['name']}]({deep_link})
                """
            
            else:
                return f"""
                **Redirecting to {tool_info['name']}**
                
                This tool will help you {tool_info['description'].lower()}. It typically takes {tool_info['estimated_time']} to complete.
                
                **What you'll get:**
                • {tool_info['output']}
                
                [Click here to start]({deep_link})
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
    
 