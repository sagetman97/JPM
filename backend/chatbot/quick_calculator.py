import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from .schemas import ConversationContext, KnowledgeLevel
from .config import config
from .backend_integration import LifeInsuranceCalculator, BackendAPIIntegrator

logger = logging.getLogger(__name__)

class QuickCalculator:
    """Handles quick insurance needs calculation with conversational flow"""
    
    def __init__(self):
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
        
        # Initialize backend integration
        self.backend_integrator = BackendAPIIntegrator()
        self.life_insurance_calc = LifeInsuranceCalculator(self.backend_integrator)
        
        # Standard questions for quick calculation
        self.standard_questions = [
            {
                "id": "age",
                "question": "What is your age?",
                "type": "number",
                "required": True,
                "validation": {"min": 18, "max": 85}
            },
            {
                "id": "income",
                "question": "What is your annual income?",
                "type": "currency",
                "required": True,
                "validation": {"min": 10000, "max": 10000000}
            },
            {
                "id": "dependents",
                "question": "How many dependents do you have?",
                "type": "number",
                "required": True,
                "validation": {"min": 0, "max": 10}
            },
            {
                "id": "debt",
                "question": "What is your total debt (mortgage, loans, etc.)?",
                "type": "currency",
                "required": True,
                "validation": {"min": 0, "max": 10000000}
            },
            {
                "id": "goals",
                "question": "What are your main financial goals? (e.g., college funding, retirement, legacy)",
                "type": "text",
                "required": False,
                "validation": {"max_length": 500}
            }
        ]
        
        # Active calculation sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def start_calculation_session(self, session_id: str, context: ConversationContext) -> str:
        """Start a new calculation session"""
        
        try:
            # Initialize session
            self.active_sessions[session_id] = {
                "started_at": datetime.utcnow(),
                "answers": {},
                "current_question": 0,
                "status": "collecting_info",
                "context": context
            }
            
            # Generate welcome message
            welcome_message = await self._generate_welcome_message(context)
            
            return welcome_message
            
        except Exception as e:
            logger.error(f"Error starting calculation session: {e}")
            return "I'm having trouble starting the calculation. Please try again."
    
    async def process_answer(self, session_id: str, answer: str) -> str:
        """Process user's answer to a calculation question"""
        
        try:
            if session_id not in self.active_sessions:
                return "No active calculation session found. Please start a new calculation."
            
            session = self.active_sessions[session_id]
            current_q = session["current_question"]
            
            if current_q >= len(self.standard_questions):
                return "All questions have been answered. Let me calculate your insurance needs."
            
            # Get current question
            question = self.standard_questions[current_q]
            
            # Validate answer
            validation_result = self._validate_answer(answer, question)
            if not validation_result["valid"]:
                return f"Please provide a valid answer: {validation_result['message']}"
            
            # Store answer
            session["answers"][question["id"]] = answer
            
            # Move to next question
            session["current_question"] += 1
            
            # Check if we have all required answers
            if self._has_sufficient_info(session):
                return await self._complete_calculation(session_id)
            else:
                # Ask next question
                return await self._ask_next_question(session_id)
                
        except Exception as e:
            logger.error(f"Error processing answer: {e}")
            return "I encountered an error processing your answer. Please try again."
    
    def _validate_answer(self, answer: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user's answer"""
        
        try:
            if question["type"] == "number":
                value = int(answer)
                validation = question["validation"]
                
                if value < validation["min"] or value > validation["max"]:
                    return {
                        "valid": False,
                        "message": f"Please enter a number between {validation['min']} and {validation['max']}"
                    }
                
            elif question["type"] == "currency":
                # Remove currency symbols and commas
                clean_answer = answer.replace("$", "").replace(",", "")
                try:
                    value = float(clean_answer)
                    validation = question["validation"]
                    
                    if value < validation["min"] or value > validation["max"]:
                        return {
                            "valid": False,
                            "message": f"Please enter an amount between ${validation['min']:,} and ${validation['max']:,}"
                        }
                except ValueError:
                    return {
                        "valid": False,
                        "message": "Please enter a valid amount (e.g., 50000 or $50,000)"
                    }
            
            elif question["type"] == "text":
                validation = question["validation"]
                if len(answer) > validation.get("max_length", 1000):
                    return {
                        "valid": False,
                        "message": f"Please keep your answer under {validation['max_length']} characters"
                    }
            
            return {"valid": True, "message": ""}
            
        except Exception as e:
            logger.error(f"Error validating answer: {e}")
            return {"valid": False, "message": "Invalid answer format"}
    
    def _has_sufficient_info(self, session: Dict[str, Any]) -> bool:
        """Check if we have sufficient information for calculation"""
        
        required_questions = [q for q in self.standard_questions if q["required"]]
        
        for question in required_questions:
            if question["id"] not in session["answers"]:
                return False
        
        return True
    
    async def _ask_next_question(self, session_id: str) -> str:
        """Ask the next question in the sequence"""
        
        try:
            session = self.active_sessions[session_id]
            current_q = session["current_question"]
            
            if current_q >= len(self.standard_questions):
                return "All questions have been answered. Let me calculate your insurance needs."
            
            question = self.standard_questions[current_q]
            
            # Generate contextual question
            contextual_question = await self._generate_contextual_question(question, session["context"])
            
            return contextual_question
            
        except Exception as e:
            logger.error(f"Error asking next question: {e}")
            return "I encountered an error. Please try again."
    
    async def _complete_calculation(self, session_id: str) -> str:
        """Complete the calculation using collected information"""
        
        try:
            session = self.active_sessions[session_id]
            answers = session["answers"]
            context = session["context"]
            
            # Update session status
            session["status"] = "calculating"
            
            # Extract values for calculation
            age = int(answers["age"])
            income = float(answers["income"].replace("$", "").replace(",", ""))
            dependents = int(answers["dependents"])
            debt = float(answers["debt"].replace("$", "").replace(",", ""))
            goals = answers.get("goals", "General financial protection")
            
            # Call backend calculation
            calculation_result = await self.life_insurance_calc.calculate_quick_needs(
                age=age,
                income=income,
                dependents=dependents,
                debt=debt,
                goals=goals
            )
            
            if "error" not in calculation_result:
                # Generate natural language response
                response = await self._generate_calculation_response(calculation_result, context)
                
                # Update session status
                session["status"] = "completed"
                session["calculation_result"] = calculation_result
                
                return response
            else:
                # Handle calculation error
                session["status"] = "error"
                return f"I encountered an error in the calculation: {calculation_result['error']}. Please try again or contact support."
                
        except Exception as e:
            logger.error(f"Error completing calculation: {e}")
            session["status"] = "error"
            return "I encountered an error completing the calculation. Please try again."
    
    async def _generate_welcome_message(self, context: ConversationContext) -> str:
        """Generate welcome message for calculation session"""
        
        try:
            prompt = self._build_welcome_prompt(context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating welcome message: {e}")
            return self._get_default_welcome_message()
    
    def _build_welcome_prompt(self, context: ConversationContext) -> str:
        """Build prompt for welcome message generation"""
        
        return f"""
        Generate a welcoming message to start an insurance needs calculation:
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'Insurance Planning'}
        - Previous Themes: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        
        **Calculation Process:**
        - We'll ask 5 simple questions about your situation
        - This will take about 2-3 minutes
        - We'll provide an estimated coverage amount and monthly premium
        - This is for educational purposes only
        
        **Questions We'll Ask:**
        1. Your age
        2. Annual income
        3. Number of dependents
        4. Total debt
        5. Financial goals
        
        **Generate a friendly, professional welcome message that:**
        - Explains the process clearly
        - Sets appropriate expectations
        - Makes the user feel comfortable
        - Emphasizes this is for educational purposes
        - Asks if they're ready to begin
        
        Welcome message:
        """
    
    def _get_default_welcome_message(self) -> str:
        """Get default welcome message if LLM fails"""
        
        return """Welcome! I'm going to help you get a quick estimate of your life insurance needs.

This will take just a few minutes and involves answering 5 simple questions about your financial situation. The result will be an estimated coverage amount and monthly premium for educational purposes.

**What we'll cover:**
• Your age and income
• Number of dependents
• Total debt obligations
• Financial goals

**Important:** This is for educational purposes only. For personalized advice, please consult with a licensed insurance professional.

Are you ready to begin? Let's start with your age - how old are you?"""
    
    async def _generate_contextual_question(self, question: Dict[str, Any], context: ConversationContext) -> str:
        """Generate contextual question based on user's knowledge level"""
        
        try:
            prompt = self._build_contextual_question_prompt(question, context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating contextual question: {e}")
            return question["question"]
    
    def _build_contextual_question_prompt(self, question: Dict[str, Any], context: ConversationContext) -> str:
        """Build prompt for contextual question generation"""
        
        return f"""
        Generate a contextual question for insurance needs calculation:
        
        **Question Details:**
        - Question ID: {question['id']}
        - Base Question: "{question['question']}"
        - Type: {question['type']}
        - Required: {question['required']}
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'Insurance Planning'}
        
        **Generate a question that:**
        - Is clear and easy to understand
        - Matches the user's knowledge level
        - Provides helpful context if needed
        - Feels natural and conversational
        
        **For different knowledge levels:**
        - Beginner: Simple language, basic explanations
        - Intermediate: Standard terminology, some context
        - Expert: Professional language, concise
        
        Contextual question:
        """
    
    async def _generate_calculation_response(self, result: Dict[str, Any], context: ConversationContext) -> str:
        """Generate natural language response for calculation results"""
        
        try:
            prompt = self._build_calculation_response_prompt(result, context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating calculation response: {e}")
            return self._get_default_calculation_response(result)
    
    def _build_calculation_response_prompt(self, result: Dict[str, Any], context: ConversationContext) -> str:
        """Build prompt for calculation response generation"""
        
        return f"""
        Generate a natural, helpful response for insurance needs calculation results:
        
        **Calculation Results:**
        - Recommended Coverage: ${result.get('recommended_coverage', 0):,}
        - Monthly Premium Estimate: ${result.get('monthly_premium_estimate', 0):,}
        - Calculation Method: {result.get('calculation_method', 'Standard Method')}
        - Key Factors: {', '.join(result.get('key_factors', []))}
        - Next Steps: {', '.join(result.get('next_steps', []))}
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Previous Questions: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        
        **Response Requirements:**
        - Explain results clearly and naturally
        - Provide context about what the numbers mean
        - Offer next steps or additional questions
        - Match user's knowledge level
        - Include appropriate disclaimers
        
        **Response Style:**
        - Beginner: Clear explanations with examples
        - Intermediate: Insights and deeper analysis
        - Expert: Professional summary with key points
        
        Natural response:
        """
    
    def _get_default_calculation_response(self, result: Dict[str, Any]) -> str:
        """Get default calculation response if LLM fails"""
        
        coverage = result.get('recommended_coverage', 0)
        premium = result.get('monthly_premium_estimate', 0)
        method = result.get('calculation_method', 'Standard Method')
        
        return f"""Great! I've calculated your insurance needs based on the information you provided.

**Your Results:**
• **Recommended Coverage:** ${coverage:,}
• **Estimated Monthly Premium:** ${premium:,}
• **Calculation Method:** {method}

**What This Means:**
This coverage amount is designed to help protect your family's financial future by covering income replacement, debt obligations, and other financial needs.

**Key Factors Considered:**
• Your age and income
• Number of dependents
• Total debt obligations
• Financial goals

**Next Steps:**
• This is an estimate for educational purposes
• Consider consulting with a licensed insurance professional
• Review your coverage needs regularly as life circumstances change
• Compare different insurance products and providers

**Important Disclaimer:** This calculation is for educational purposes only and should not be considered as specific financial advice. Please consult with a licensed insurance professional for personalized recommendations.

Would you like to learn more about different types of life insurance or have questions about the calculation?"""
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of calculation session"""
        
        if session_id not in self.active_sessions:
            return {"status": "not_found"}
        
        session = self.active_sessions[session_id]
        return {
            "status": session["status"],
            "current_question": session["current_question"],
            "total_questions": len(self.standard_questions),
            "answers_provided": len(session["answers"]),
            "started_at": session["started_at"].isoformat(),
            "calculation_result": session.get("calculation_result", {})
        }
    
    async def reset_session(self, session_id: str) -> str:
        """Reset a calculation session"""
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return "Calculation session reset successfully. You can start a new calculation."
        else:
            return "No active session found to reset."
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old calculation sessions"""
        
        try:
            current_time = datetime.utcnow()
            sessions_to_remove = []
            
            for session_id, session in self.active_sessions.items():
                age_hours = (current_time - session["started_at"]).total_seconds() / 3600
                if age_hours > max_age_hours:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
            
            logger.info(f"Cleaned up {len(sessions_to_remove)} old calculation sessions")
            return len(sessions_to_remove)
            
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
            return 0
    
    async def close(self):
        """Clean up resources"""
        
        await self.backend_integrator.close() 