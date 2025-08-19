import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from .schemas import (
    ChatMessage, ChatResponse, ConversationContext, IntentResult,
    RoutingDecision, RAGResult, SearchResult, QualityScore,
    ComplianceResult, ChatSession, MessageType
)
from .config import config

logger = logging.getLogger(__name__)

class BaseLLMResponse:
    """Handles base LLM responses for fallback and general knowledge"""
    
    def __init__(self):
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
    
    async def generate_safe_response(self, query: str, context: ConversationContext) -> str:
        """Generate safe, educational response using base LLM"""
        
        try:
            prompt = self._build_safe_response_prompt(query, context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating base LLM response: {e}")
            return self._get_fallback_response(query)
    
    def _build_safe_response_prompt(self, query: str, context: ConversationContext) -> str:
        """Build safe prompt for base LLM"""
        
        return f"""
        You are a knowledgeable financial advisor assistant specializing in life insurance and financial planning.
        
        **User Question:** "{query}"
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Focus Area: {context.current_topic or 'General'}
        - Previous Themes: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        
        **Response Guidelines:**
        1. **Educational Focus**: Provide educational information about life insurance and financial planning
        2. **General Knowledge**: Use your general knowledge to provide helpful insights
        3. **Professional Tone**: Maintain professional financial advisory language
        4. **Safety First**: Avoid specific financial advice, focus on education and general principles
        5. **Context Awareness**: Consider the user's knowledge level and previous conversation
        6. **Life Insurance Expertise**: Leverage your knowledge of life insurance products, strategies, and planning
        
        **Response Structure:**
        - Direct answer to their question
        - Educational explanation of relevant concepts
        - General principles and best practices
        - Suggestions for further exploration
        - Next steps or considerations
        
        **Important:**
        - Focus on educational value, not specific financial advice
        - Emphasize the importance of working with licensed professionals
        - Provide general information that applies to most situations
        - Encourage further research and professional consultation
        
        Generate a helpful, educational response:
        """
    
    def _get_fallback_response(self, query: str) -> str:
        """Get fallback response when LLM fails"""
        
        return f"""
        I understand you're asking about "{query}" related to life insurance and financial planning.
        
        While I'm experiencing some technical difficulties right now, I can provide some general guidance:
        
        **General Principles:**
        • Life insurance is a key component of comprehensive financial planning
        • Coverage needs vary based on individual circumstances and goals
        • It's important to work with licensed professionals for personalized advice
        • Regular reviews of insurance coverage are essential as life circumstances change
        
        **Next Steps:**
        • Consider scheduling a consultation with a licensed insurance professional
        • Review your current financial situation and protection needs
        • Research different types of life insurance products
        • Evaluate how insurance fits into your overall financial strategy
        
        Would you like to try asking your question again, or would you prefer to explore a different topic?
        """

class QualityEvaluator:
    """Evaluates response quality and provides improvement suggestions"""
    
    def __init__(self):
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
    
    async def evaluate_response_quality(self, query: str, response: str, context: ConversationContext) -> QualityScore:
        """Evaluate response quality using semantic understanding"""
        
        try:
            prompt = self._build_quality_evaluation_prompt(query, response, context)
            
            evaluation = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            quality_score = self._parse_quality_evaluation(evaluation.choices[0].message.content)
            return quality_score
            
        except Exception as e:
            logger.error(f"Error evaluating response quality: {e}")
            return QualityScore(
                overall_score=0.7,
                relevance_score=0.7,
                accuracy_score=0.7,
                completeness_score=0.7,
                clarity_score=0.7,
                improvement_areas=["Quality evaluation unavailable"]
            )
    
    def _build_quality_evaluation_prompt(self, query: str, response: str, context: ConversationContext) -> str:
        """Build prompt for quality evaluation"""
        
        return f"""
        Evaluate the quality of this financial advice response:
        
        **User Question:** "{query}"
        
        **Generated Response:** "{response}"
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'General'}
        - Previous Themes: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        
        **Quality Criteria (Rate 0-1 for each):**
        1. **Relevance**: Does the response directly address the question?
        2. **Accuracy**: Is the information correct and reliable?
        3. **Completeness**: Does it cover the full scope of the question?
        4. **Clarity**: Is the response clear and understandable?
        5. **Educational Value**: Does it provide useful insights?
        6. **Context Appropriateness**: Does it match the user's knowledge level?
        
        **Return JSON with scores and improvement areas:**
        {{
            "relevance_score": 0.9,
            "accuracy_score": 0.8,
            "completeness_score": 0.7,
            "clarity_score": 0.9,
            "educational_value_score": 0.8,
            "context_appropriateness_score": 0.9,
            "overall_score": 0.83,
            "improvement_areas": ["Could provide more specific examples", "Consider adding next steps"]
        }}
        """
    
    def _parse_quality_evaluation(self, evaluation: str) -> QualityScore:
        """Parse quality evaluation response"""
        
        try:
            import json
            
            # Try to extract JSON
            start_idx = evaluation.find('{')
            end_idx = evaluation.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = evaluation[start_idx:end_idx]
                eval_data = json.loads(json_str)
                
                return QualityScore(
                    overall_score=float(eval_data.get("overall_score", 0.7)),
                    relevance_score=float(eval_data.get("relevance_score", 0.7)),
                    accuracy_score=float(eval_data.get("accuracy_score", 0.7)),
                    completeness_score=float(eval_data.get("completeness_score", 0.7)),
                    clarity_score=float(eval_data.get("clarity_score", 0.7)),
                    improvement_areas=eval_data.get("improvement_areas", [])
                )
            
        except Exception as e:
            logger.error(f"Error parsing quality evaluation: {e}")
        
        # Return default quality score
        return QualityScore(
            overall_score=0.7,
            relevance_score=0.7,
            accuracy_score=0.7,
            completeness_score=0.7,
            clarity_score=0.7,
            improvement_areas=["Quality evaluation unavailable"]
        )

class ComplianceAgent:
    """Ensures compliance with financial regulations and legal requirements"""
    
    def __init__(self):
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
    
    async def review_response(self, response: str, context: ConversationContext) -> ComplianceResult:
        """Review response for compliance and safety"""
        
        try:
            prompt = self._build_compliance_review_prompt(response, context)
            
            review = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            compliance_result = self._parse_compliance_review(review.choices[0].message.content, response)
            return compliance_result
            
        except Exception as e:
            logger.error(f"Error in compliance review: {e}")
            # Return safe compliance result
            return ComplianceResult(
                original_response=response,
                final_response=response,
                legal_compliance=True,
                risk_assessment="low",
                disclaimers=["This information is for educational purposes only. Please consult with a licensed professional for personalized advice."],
                was_rewritten=False
            )
    
    def _build_compliance_review_prompt(self, response: str, context: ConversationContext) -> str:
        """Build prompt for compliance review"""
        
        return f"""
        Review this financial advice response for compliance and safety:
        
        **Response:** "{response}"
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'General'}
        
        **Compliance Review Required:**
        1. **Legal Compliance**: Does this meet financial advisory regulations?
        2. **Risk Assessment**: What are the potential risks?
        3. **Disclaimers Needed**: What legal disclaimers should be added?
        4. **Response Safety**: Is this response safe and appropriate?
        
        **Return JSON with compliance assessment:**
        {{
            "legal_compliance": true,
            "risk_assessment": "low|medium|high",
            "disclaimers_needed": ["disclaimer1", "disclaimer2"],
            "response_safe": true,
            "needs_rewriting": false,
            "rewritten_response": "original response if no changes needed"
        }}
        
        **Compliance Guidelines:**
        - Avoid specific financial advice
        - Include appropriate disclaimers
        - Emphasize professional consultation
        - Focus on educational content
        """
    
    def _parse_compliance_review(self, review: str, original_response: str) -> ComplianceResult:
        """Parse compliance review response"""
        
        try:
            import json
            
            # Try to extract JSON
            start_idx = review.find('{')
            end_idx = review.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = review[start_idx:end_idx]
                review_data = json.loads(json_str)
                
                needs_rewriting = review_data.get("needs_rewriting", False)
                final_response = review_data.get("rewritten_response", original_response) if needs_rewriting else original_response
                
                return ComplianceResult(
                    original_response=original_response,
                    final_response=final_response,
                    legal_compliance=review_data.get("legal_compliance", True),
                    risk_assessment=review_data.get("risk_assessment", "low"),
                    disclaimers=review_data.get("disclaimers_needed", []),
                    was_rewritten=needs_rewriting
                )
            
        except Exception as e:
            logger.error(f"Error parsing compliance review: {e}")
        
        # Return safe compliance result
        return ComplianceResult(
            original_response=original_response,
            final_response=original_response,
            legal_compliance=True,
            risk_assessment="low",
            disclaimers=["This information is for educational purposes only. Please consult with a licensed professional for personalized advice."],
            was_rewritten=False
        )

class ChatbotOrchestrator:
    """Orchestrates the entire chatbot pipeline"""
    
    def __init__(self, intent_classifier, smart_router, rag_system, external_search, tool_integrator, calculator_selector, quick_calculator, file_processor):
        self.intent_classifier = intent_classifier
        self.smart_router = smart_router
        self.rag_system = rag_system
        self.external_search = external_search
        self.tool_integrator = tool_integrator
        self.calculator_selector = calculator_selector
        self.quick_calculator = quick_calculator
        self.file_processor = file_processor
        
        # Initialize response components
        self.base_llm = BaseLLMResponse()
        self.quality_evaluator = QualityEvaluator()
        self.compliance_agent = ComplianceAgent()
        
        # Session management
        self.sessions: Dict[str, ChatSession] = {}
        
        logger.info("ChatbotOrchestrator initialized successfully")
    
    async def process_message(self, message: ChatMessage, session_id: str) -> ChatResponse:
        """Process a chat message through the complete pipeline"""
        
        try:
            # Get or create session
            session = self._get_or_create_session(session_id)
            
            # Add message to session
            session.add_message(message)
            
            # Process through pipeline
            response = await self._process_through_pipeline(message, session)
            
            # Add response to session
            session.add_message(response)
            
            logger.info(f"Message processed successfully for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    def _get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one"""
        
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(
                session_id=session_id,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
        
        # Update last activity
        self.sessions[session_id].last_activity = datetime.utcnow()
        return self.sessions[session_id]
    
    async def _process_through_pipeline(self, message: ChatMessage, session: ChatSession) -> ChatResponse:
        """Process message through the complete semantic pipeline"""
        
        try:
            # Step 1: Intent Classification
            intent_result = await self.intent_classifier.classify_intent_semantically(
                message.content, session.get_context()
            )
            
            # Step 2: Smart Routing
            routing_decision = await self.smart_router.route_query_semantically(
                intent_result, session.get_context()
            )
            
            # Step 3: Response Generation
            response_content = await self._generate_response_content(
                routing_decision, message.content, session.get_context()
            )
            
            # Step 4: Quality Evaluation
            quality_score = await self.quality_evaluator.evaluate_response_quality(
                message.content, response_content, session.get_context()
            )
            
            # Step 5: Compliance Review
            compliance_result = await self.compliance_agent.review_response(
                response_content, session.get_context()
            )
            
            # Create final response
            return ChatResponse(
                id=str(uuid.uuid4()),
                type=MessageType.ASSISTANT,
                content=compliance_result.final_response,
                timestamp=datetime.utcnow(),
                quality_score=quality_score.overall_score,
                routing_decision=routing_decision,
                disclaimers=compliance_result.disclaimers,
                session_id=session.session_id
            )
            
        except Exception as e:
            logger.error(f"Error in pipeline processing: {e}")
            # Fallback to base LLM
            fallback_content = await self.base_llm.generate_safe_response(
                message.content, session.get_context()
            )
            
            return ChatResponse(
                id=str(uuid.uuid4()),
                type=MessageType.ASSISTANT,
                content=fallback_content,
                timestamp=datetime.utcnow(),
                quality_score=0.6,
                routing_decision=RoutingDecision(
                    route_type="fallback",
                    confidence=0.6,
                    reasoning="Pipeline error, using fallback response"
                ),
                disclaimers=["This response was generated due to a system error. Please consult with a licensed professional for personalized advice."],
                session_id=session.session_id
            )
    
    async def _generate_response_content(self, routing_decision: RoutingDecision, query: str, context: ConversationContext) -> str:
        """Generate response content based on routing decision"""
        
        try:
            if routing_decision.route_type.value == "rag":
                # Use RAG system
                rag_result = await self.rag_system.get_semantic_response(query, context)
                return rag_result.response
                
            elif routing_decision.route_type.value == "external_search":
                # Use external search
                search_result = await self.external_search.search_with_evaluation(query, context)
                return search_result.response
                
            elif routing_decision.route_type.value == "quick_calculator":
                # Use quick calculator
                return await self._handle_quick_calculator(query, context)
                
            elif routing_decision.route_type.value == "external_tool":
                # Route to external tool
                tool_response = await self.tool_integrator.route_to_external_tool(
                    routing_decision.tool_type, context
                )
                return tool_response.message
                
            else:
                # Fallback to base LLM
                return await self.base_llm.generate_safe_response(query, context)
                
        except Exception as e:
            logger.error(f"Error generating response content: {e}")
            return await self.base_llm.generate_safe_response(query, context)
    
    async def _handle_quick_calculator(self, query: str, context: ConversationContext) -> str:
        """Handle quick calculator requests"""
        
        try:
            # Check if we have enough information for calculation
            if await self.quick_calculator.has_sufficient_info(query, context):
                # Perform calculation
                result = await self.quick_calculator.calculate_needs(query, context)
                return result
            else:
                # Ask for more information
                return await self.quick_calculator.get_clarification_questions(query, context)
                
        except Exception as e:
            logger.error(f"Error in quick calculator: {e}")
            return "I'm having trouble with the calculation right now. Please try again or contact a licensed professional for assistance."
    
    async def process_file_upload(self, file_data: bytes, filename: str, session_id: str) -> Dict[str, Any]:
        """Process file upload for analysis"""
        
        try:
            session = self._get_or_create_session(session_id)
            context = session.get_context()
            
            # Process file upload
            file_upload = await self.file_processor.process_uploaded_file(file_data, filename, context)
            
            return {
                "status": "success",
                "file_id": file_upload.file_id,
                "filename": file_upload.filename,
                "file_type": file_upload.file_type,
                "message": f"File '{filename}' uploaded successfully and ready for analysis."
            }
            
        except Exception as e:
            logger.error(f"Error processing file upload: {e}")
            return {
                "status": "error",
                "message": f"Error processing file: {str(e)}"
            }
    
    async def analyze_uploaded_file(self, file_id: str, query: str, session_id: str) -> str:
        """Analyze uploaded file in context of conversation"""
        
        try:
            session = self._get_or_create_session(session_id)
            context = session.get_context()
            
            # Analyze file
            analysis = await self.file_processor.analyze_file_in_context(file_id, query, context)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            return f"Error analyzing file: {str(e)}"
    
    def get_file_summary(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of uploaded file"""
        
        try:
            return self.file_processor.get_file_summary(file_id)
        except Exception as e:
            logger.error(f"Error getting file summary: {e}")
            return None
    
    def cleanup_files(self, max_age_hours: int = 24) -> int:
        """Clean up old uploaded files"""
        
        try:
            return self.file_processor.cleanup_old_files(max_age_hours)
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
            return 0
    
    def _create_error_response(self, original_message: ChatMessage, error_message: str) -> ChatResponse:
        """Create error response when processing fails"""
        
        return ChatResponse(
            id=str(uuid.uuid4()),
            type=MessageType.ASSISTANT,
            content=f"I'm sorry, I encountered an error while processing your message: {error_message}. Please try again or contact support if the problem persists.",
            timestamp=datetime.utcnow(),
            quality_score=0.0,
            routing_decision=RoutingDecision(
                route_type="error",
                confidence=0.0,
                reasoning="System error occurred"
            ),
            disclaimers=["This response indicates a system error. Please try again or contact support."],
            session_id=original_message.session_id if hasattr(original_message, 'session_id') else "unknown"
        ) 