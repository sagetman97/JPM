"""
Quick calculator for life insurance needs assessment.
Handles in-chat calculations with user interaction.
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from openai import AsyncOpenAI
from .schemas import ConversationContext, KnowledgeLevel, CalculatorType
from .config import config
from .backend_integration import LifeInsuranceCalculator, BackendAPIIntegrator

logger = logging.getLogger(__name__)

class QuickCalculator:
    """Handles quick insurance needs calculation with conversational flow"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
        
        # Initialize backend integration
        self.backend_integrator = BackendAPIIntegrator()
        self.life_insurance_calc = LifeInsuranceCalculator(self.backend_integrator)
        
        # Standard questions matching the frontend quick calculator
        self.standard_questions = [
            {
                "id": "age",
                "question": "What is your age?",
                "type": "number",
                "required": True,
                "validation": {"min": 18, "max": 85}
            },
            {
                "id": "marital_status",
                "question": "What is your marital status?",
                "type": "select",
                "required": True,
                "options": ["Single", "Married", "Divorced", "Widowed"],
                "validation": {}
            },
            {
                "id": "dependents",
                "question": "How many dependents do you have?",
                "type": "number",
                "required": True,
                "validation": {"min": 0, "max": 10}
            },
            {
                "id": "monthly_income",
                "question": "What is your monthly income? (e.g., $5,000)",
                "type": "currency",
                "required": True,
                "validation": {"min": 1000, "max": 1000000}
            },
            {
                "id": "mortgage_balance",
                "question": "What is your total debt (mortgage, loans, etc.)? (e.g., $300,000)",
                "type": "currency",
                "required": True,
                "validation": {"min": 0, "max": 10000000}
            },
            {
                "id": "total_assets",
                "question": "What are your estimated total assets (savings, investments, etc.)? (e.g., $150,000)",
                "type": "currency",
                "required": True,
                "validation": {"min": 0, "max": 10000000}
            },
            {
                "id": "provide_education",
                "question": "Do you want to provide for your children's education? (yes/no)",
                "type": "boolean",
                "required": False,
                "validation": {}
            },
            {
                "id": "individual_life",
                "question": "How much individual life insurance do you currently have? (e.g., $100,000 or 0 if none)",
                "type": "currency",
                "required": False,
                "validation": {"min": 0, "max": 10000000}
            },
            {
                "id": "group_life",
                "question": "How much group life insurance do you currently have? (e.g., $50,000 or 0 if none)",
                "type": "currency",
                "required": False,
                "validation": {"min": 0, "max": 10000000}
            },
            {
                "id": "cash_value_importance",
                "question": "Is accumulating savings in your life insurance policy important to you? (yes/no/unsure)",
                "type": "select",
                "required": False,
                "options": ["yes", "no", "unsure"],
                "validation": {}
            },
            {
                "id": "permanent_coverage",
                "question": "Do you want permanent lifelong coverage? (yes/no/unsure)",
                "type": "select",
                "required": False,
                "options": ["yes", "no", "unsure"],
                "validation": {}
            },
            {
                "id": "income_replacement_years",
                "question": "How many years of income replacement do you want? (5-20 years, default 10)",
                "type": "number",
                "required": False,
                "validation": {"min": 5, "max": 20}
            }
        ]
        
        # Active calculator sessions
        self.active_sessions = {}
        
        # Question type handlers
        self.question_types = {
            "age": "number",
            "marital_status": "select", 
            "dependents": "number",
            "monthly_income": "currency",
            "mortgage_balance": "currency",
            "other_debts": "currency",
            "provide_education": "boolean",
            "individual_life": "currency",
            "group_life": "currency",
            "cash_value_importance": "select"
        }
    
    def _validate_number(self, value: str, validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate numeric input"""
        try:
            num_value = float(value.replace(',', '').replace('$', ''))
            min_val = validation.get('min', 0)
            max_val = validation.get('max', float('inf'))
            
            if num_value < min_val or num_value > max_val:
                return {
                    "valid": False,
                    "message": f"Value must be between {min_val} and {max_val}"
                }
            
            return {"valid": True, "value": num_value}
        except ValueError:
            return {"valid": False, "message": "Please enter a valid number"}
    
    def _validate_currency(self, value: str, validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate currency input"""
        return self._validate_number(value, validation)
    
    def _validate_text(self, value: str, validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate text input"""
        max_length = validation.get('max_length', 1000)
        
        if len(value) > max_length:
            return {
                "valid": False,
                "message": f"Text must be {max_length} characters or less"
            }
        
        return {"valid": True, "value": value} 

    async def start_calculation_session(self, session_id: str, context: ConversationContext) -> str:
        """Start a new calculation session"""
        try:
            # Initialize calculator session in context
            context.calculator_state = "active"
            context.calculator_type = CalculatorType.QUICK
            context.calculator_session = {
                "session_id": session_id,
                "started_at": datetime.utcnow().isoformat(),
                "current_question_index": 0,
                "answers": {},
                "status": "active"
            }
            
            # Store session in active_sessions for backup
            self.active_sessions[session_id] = context.calculator_session
            
            # Generate welcome message
            welcome_message = await self._generate_welcome_message(context)
            
            # Ask first question
            first_question = await self._ask_next_question(context)
            
            # Return a formatted string response instead of a dictionary
            return f"{welcome_message}\n\n{first_question}"
            
        except Exception as e:
            logger.error(f"Error starting calculation session: {e}")
            return "I'm sorry, I encountered an error starting the calculation session. Please try again."

    async def process_answer(self, answer: str, context: ConversationContext) -> Dict[str, Any]:
        """Process user's answer to a calculator question"""
        try:
            logger.info(f"🧮 Processing answer: '{answer}'")
            
            # Get current session from context
            session = context.calculator_session
            if not session:
                logger.error("🧮 No active calculator session found")
                return {
                    "status": "error",
                    "message": "No active calculator session found"
                }
            
            current_question_index = session.get("current_question_index", 0)
            logger.info(f"🧮 Current question index: {current_question_index}, total questions: {len(self.standard_questions)}")
            
            if current_question_index >= len(self.standard_questions):
                logger.info("🧮 All questions answered, completing calculation...")
                return await self._complete_calculation(context)
            
            current_question = self.standard_questions[current_question_index]
            question_id = current_question["id"]
            logger.info(f"🧮 Processing question: {question_id}")
            
            # Parse and validate the answer
            parsed_answer = await self._semantically_parse_answer(answer, current_question)
            logger.info(f"🧮 Parsed answer: {parsed_answer}")
            
            if parsed_answer["valid"]:
                # Store the answer
                session["answers"][question_id] = parsed_answer["value"]
                session["current_question_index"] += 1
                logger.info(f"🧮 Stored answer for {question_id}: {parsed_answer['value']}")
                logger.info(f"🧮 Updated question index to: {session['current_question_index']}")
                logger.info(f"🧮 Total answers stored: {len(session['answers'])}")
                
                # Check if we have enough information
                has_sufficient = await self._has_sufficient_info(session)
                logger.info(f"🧮 Has sufficient info: {has_sufficient}")
                
                if has_sufficient:
                    logger.info("🧮 Sufficient info, completing calculation...")
                    return await self._complete_calculation(context)
                else:
                    # Ask next question
                    logger.info("🧮 Not enough info, asking next question...")
                    next_question = await self._ask_next_question(context)
                    return {
                        "status": "question",
                        "message": f"Thank you! {next_question}",
                        "question": next_question,
                        "progress": f"{session['current_question_index']}/{len(self.standard_questions)} questions completed"
                    }
            else:
                # Handle validation failure
                logger.warning(f"🧮 Validation failed for {question_id}: {parsed_answer}")
                return await self._handle_validation_failure(current_question, answer, parsed_answer, context)
                
        except Exception as e:
            logger.error(f"🧮 Error processing answer: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": "Failed to process answer",
                "error": str(e)
            }

    async def _ask_next_question(self, context_or_session_id) -> str:
        """Ask the next question in the sequence"""
        try:
            # Handle both context and session_id
            if isinstance(context_or_session_id, ConversationContext):
                session = context_or_session_id.calculator_session
                if not session:
                    return "No active calculator session found. Please start a new calculation."
            else:
                session = self.active_sessions.get(context_or_session_id)
            
            if not session:
                return "No active calculator session found."
            
            current_question_index = session.get("current_question_index", 0)
            
            if current_question_index >= len(self.standard_questions):
                return "All questions have been answered. Calculating your insurance needs..."
            
            current_question = self.standard_questions[current_question_index]
            
            # Generate contextual question
            contextual_question = await self._generate_contextual_question(current_question, context_or_session_id)
            
            return contextual_question
            
        except Exception as e:
            logger.error(f"🧮 Error asking next question: {e}")
            return "Error generating question. Please try again."

    async def _has_sufficient_info(self, session: Dict[str, Any]) -> bool:
        """Check if we have enough information to complete the calculation"""
        try:
            required_questions = [q for q in self.standard_questions if q.get("required", True)]
            answered_required = all(q["id"] in session["answers"] for q in required_questions)
            
            # Also check if we have at least 6 questions answered for a reasonable calculation
            total_answered = len(session["answers"])
            
            # Check if we have current life insurance information (important for accurate calculation)
            has_current_coverage_info = (
                "individual_life" in session["answers"] and 
                "group_life" in session["answers"]
            )
            
            logger.info(f"🧮 Sufficient info check - required questions: {[q['id'] for q in required_questions]}")
            logger.info(f"🧮 Sufficient info check - session answers: {list(session.get('answers', {}).keys())}")
            logger.info(f"🧮 Sufficient info check - answered_required: {answered_required}, total_answered: {total_answered}")
            logger.info(f"🧮 Sufficient info check - has_current_coverage_info: {has_current_coverage_info}")
            
            # We need all required questions AND current coverage info for the most accurate calculation
            result = answered_required and total_answered >= 6 and has_current_coverage_info
            logger.info(f"🧮 Sufficient info check result: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"🧮 Error checking sufficient info: {e}")
            return False

    async def _complete_calculation(self, context: ConversationContext) -> Dict[str, Any]:
        """Complete the calculation using gathered information"""
        try:
            logger.info("🧮 Starting calculation completion...")
            session = context.calculator_session
            if not session:
                logger.error("🧮 No active calculator session found")
                return {
                    "status": "error",
                    "message": "No active calculator session found"
                }
            
            logger.info(f"🧮 Session answers: {session.get('answers', {})}")
            
            # Prepare data for calculation - convert to the format expected by the backend
            age = session["answers"].get("age")
            monthly_income = session["answers"].get("monthly_income")
            dependents = session["answers"].get("dependents")
            total_debt = session["answers"].get("mortgage_balance", 0)
            total_assets = session["answers"].get("total_assets", 0)  # Fixed field name
            
            # Get current life insurance coverage information
            individual_life = session["answers"].get("individual_life", 0)
            group_life = session["answers"].get("group_life", 0)
            current_total_coverage = float(individual_life or 0) + float(group_life or 0)
            
            logger.info(f"🧮 Extracted data - age: {age}, income: {monthly_income}, dependents: {dependents}, debt: {total_debt}, assets: {total_assets}")
            logger.info(f"🧮 Current coverage - individual: {individual_life}, group: {group_life}, total: {current_total_coverage}")
            
            # Convert monthly income to annual
            annual_income = float(monthly_income) * 12 if monthly_income else 0
            
            # Determine financial goals based on answers
            goals = []
            if session["answers"].get("provide_education") == "yes":
                goals.append("education_funding")
            if session["answers"].get("cash_value_importance") == "yes":
                goals.append("cash_value_accumulation")
            if session["answers"].get("permanent_coverage") == "yes":
                goals.append("permanent_protection")
            
            goals_text = ", ".join(goals) if goals else "basic_protection"
            logger.info(f"🧮 Financial goals: {goals_text}")
            
            # Call backend calculation using the correct method
            logger.info("🧮 Calling backend calculation...")
            result = await self.life_insurance_calc.calculate_quick_needs(
                age=int(age) if age else 35,
                income=annual_income,
                dependents=int(dependents) if dependents else 0,
                debt=float(total_debt) if total_debt else 0,
                goals=goals_text
            )
            
            logger.info(f"🧮 Backend calculation result: {result}")
            
            if "error" in result:
                logger.error(f"🧮 Backend calculation error: {result['error']}")
                return {
                    "status": "error",
                    "message": f"Calculation failed: {result['error']}",
                    "error": result["error"]
                }
            
            # Generate response
            logger.info("🧮 Generating calculation response...")
            
            # Add current coverage information to the result for response generation
            result["current_coverage"] = current_total_coverage
            result["coverage_gap"] = result.get("recommended_coverage", 0) - current_total_coverage
            
            response = await self._generate_calculation_response(result)
            
            # Mark session as complete
            session["status"] = "completed"
            session["completed_at"] = datetime.utcnow().isoformat()
            session["result"] = result
            
            # Reset calculator state in context
            context.calculator_state = "inactive"
            context.calculator_session = None
            
            logger.info("🧮 Calculation completed successfully")
            
            return {
                "status": "completed",
                "message": response,
                "result": result,
                "recommendation": result.get("recommendation", "Based on your information, we recommend consulting with a licensed insurance professional.")
            }
            
        except Exception as e:
            logger.error(f"🧮 Error completing calculation: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": "Failed to complete calculation",
                "error": str(e)
            }

    async def _generate_calculation_response(self, result: Dict[str, Any]) -> str:
        """Generate a user-friendly response for the calculation result"""
        try:
            prompt = self._build_calculation_response_prompt(result)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"🧮 Error generating calculation response: {e}")
            return self._get_default_calculation_response(result)

    def _build_calculation_response_prompt(self, result: Dict[str, Any]) -> str:
        """Build prompt for calculation response generation - matching frontend results page completely"""
        try:
            # Handle the actual backend response format from quick calculation
            coverage = result.get('recommended_coverage', 0)
            monthly_premium = result.get('monthly_premium_estimate', 0)
            calculation_method = result.get('calculation_method', 'DIME + Income Replacement')
            
            # Get current coverage information
            current_coverage = result.get('current_coverage', 0)
            coverage_gap = result.get('coverage_gap', coverage)
            
            # For quick calculation, we need to determine product recommendation based on the data
            product = "JPM TermVest+ IUL Track"  # Default to IUL for better value
            rationale = f"Based on {calculation_method} methodology, considering your age, income, and dependents"
            duration_years = 20  # Default term length
            
            # Since we don't have breakdown from quick calculation, we'll estimate based on coverage
            estimated_breakdown = {
                'living_expenses': int(coverage * 0.6),  # 60% for income replacement
                'debts': int(coverage * 0.2),           # 20% for debt coverage
                'education': int(coverage * 0.1),       # 10% for education
                'funeral': 8000,                        # Standard funeral cost
                'legacy': int(coverage * 0.1),          # 10% for legacy
                'other': 0
            }
            
            # Calculate monthly savings recommendation
            monthly_savings = max(300, int(coverage * 0.0001))  # Rough estimate
            max_monthly = monthly_savings * 2  # Conservative max
            
            # Calculate savings level indicator
            percentage = 50  # Default to medium
            if max_monthly and monthly_savings:
                percentage = min((monthly_savings / max_monthly) * 100, 100)
            
            return f"""Generate a comprehensive life insurance calculation response for chat that explains the results clearly.

**Calculation Results:**
- Recommended Coverage: ${coverage:,}
- Current Coverage: ${current_coverage:,}
- Coverage Gap: ${coverage_gap:,}
- Product: {product}
- Duration: {'permanent' if 'IUL' in str(product) else f'{duration_years} years'}
- Rationale: {rationale}

**Coverage Breakdown:**
- Living Expenses: ${estimated_breakdown['living_expenses']:,}
- Debts: ${estimated_breakdown['debts']:,}
- Education: ${estimated_breakdown['education']:,}
- Funeral: ${estimated_breakdown['funeral']:,}
- Legacy: ${estimated_breakdown['legacy']:,}
- Other: ${estimated_breakdown['other']:,}

**Monthly Premium Estimate:**
- Estimated Monthly Premium: ${monthly_premium:,} (if $0, this indicates a calculation estimate)
- Recommended Monthly Savings: ${monthly_savings:,}
- Maximum Monthly Contribution: ${max_monthly:,}
- Savings Level: {percentage:.0f}% of maximum

**Key Factors:**
- Calculation Method: {calculation_method}
- Product Recommendation: {product}
- Coverage Duration: {'permanent' if 'IUL' in str(product) else f'{duration_years} years'}

**Next Steps:**
1. Review your coverage needs
2. Compare with existing coverage
3. Consider different product types
4. Consult with a licensed insurance professional

Please format this as a friendly, conversational response that explains the results clearly and provides actionable next steps."""
            
        except Exception as e:
            logger.error(f"🧮 Error building calculation response prompt: {e}")
            return "Generate a comprehensive life insurance calculation response."

    def _get_default_calculation_response(self, result: Dict[str, Any]) -> str:
        """Default calculation response matching frontend results page - chat-optimized with full details"""
        try:
            # Handle the actual backend response format from quick calculation
            coverage = result.get('recommended_coverage', 0)
            monthly_premium = result.get('monthly_premium_estimate', 0)
            calculation_method = result.get('calculation_method', 'DIME + Income Replacement')
            
            # Get current coverage from the session context (we'll need to pass this through)
            # For now, we'll assume no current coverage since this is a quick calculation
            current_coverage = result.get('current_coverage', 0)  # This now comes from the result
            coverage_gap = result.get('coverage_gap', coverage)  # This now comes from the result
            
            # For quick calculation, we need to determine product recommendation based on the data
            # Since we don't have detailed breakdown, we'll make a reasonable assumption
            product = "JPM TermVest+ IUL Track"  # Default to IUL for better value
            rationale = f"Based on {calculation_method} methodology, considering your age, income, and dependents"
            duration_years = 20  # Default term length
            
            # Since we don't have breakdown from quick calculation, we'll estimate based on coverage
            estimated_breakdown = {
                'living_expenses': int(coverage * 0.6),  # 60% for income replacement
                'debts': int(coverage * 0.2),           # 20% for debt coverage
                'education': int(coverage * 0.1),       # 10% for education
                'funeral': 8000,                        # Standard funeral cost
                'legacy': int(coverage * 0.1),          # 10% for legacy
                'other': 0
            }
            
            # Calculate monthly savings recommendation (2-3% of monthly income)
            # We'll estimate based on the coverage amount
            monthly_savings = max(300, int(coverage * 0.0001))  # Rough estimate
            max_monthly = monthly_savings * 2  # Conservative max
            
            # Calculate savings level indicator
            percentage = 50  # Default to medium
            if max_monthly and monthly_savings:
                percentage = min((monthly_savings / max_monthly) * 100, 100)
            
            savings_level = ""
            savings_color = ""
            if percentage <= 25:
                savings_level = "Low Savings"
                savings_color = "🟠"
            elif percentage <= 50:
                savings_level = "Medium Savings"
                savings_color = "🔵"
            elif percentage <= 75:
                savings_level = "High Savings"
                savings_color = "🟢"
            else:
                savings_level = "Maximum Savings"
                savings_color = "🟣"
            
            # Product-specific explanations
            if 'IUL' in str(product):
                product_explanation = "JPM TermVest+ offers two tracks: Term and IUL. The IUL Track provides immediate access to cash value accumulation with tax-deferred growth potential, flexible premiums, and permanent coverage. Your cash value can grow based on market performance while providing a guaranteed death benefit for life."
                duration_display = "permanent"
            else:
                product_explanation = "JPM TermVest+ offers two tracks: Term and IUL. The Term Track provides essential protection at an affordable premium for a specified period. You can convert to the IUL Track later to begin building cash value savings with permanent coverage when your financial situation allows."
                duration_display = f"{duration_years} years"
            
            # Chat-optimized response matching frontend results page completely
            response = f"""🎉 **Your Life Insurance Needs Calculation is Complete!**

**📊 SUMMARY CARDS:**
• **Recommended Coverage:** ${coverage:,}
• **Current Coverage:** ${current_coverage:,}
• **Coverage Gap:** ${coverage_gap:,}
• **Duration:** {duration_display}

**🏆 PRODUCT RECOMMENDATION:**
**{product}**

{product_explanation}

**Why this product?** {rationale}

**📋 COVERAGE BREAKDOWN:**
• Living Expenses: ${estimated_breakdown['living_expenses']:,}
• Debts: ${estimated_breakdown['debts']:,}
• Education: ${estimated_breakdown['education']:,}
• Funeral: ${estimated_breakdown['funeral']:,}
• Legacy: ${estimated_breakdown['legacy']:,}
• Other: ${estimated_breakdown['other']:,}

**💰 MONTHLY PREMIUM DETAILS:**
• **Estimated Monthly Premium:** ${monthly_premium:,} (if $0, this indicates a calculation estimate)
• **Recommended Monthly Savings:** ${monthly_savings:,}
• **Maximum Monthly Contribution:** ${max_monthly:,}

**💡 WHAT THIS MEANS:**
The MEC (Modified Endowment Contract) limit is the maximum monthly contribution that keeps your policy from becoming a modified endowment contract, which has different tax implications.

**📈 SAVINGS LEVEL INDICATOR:**
{savings_color} **{savings_level}** ({percentage:.0f}% of maximum)

**🎯 PROJECTION ASSUMPTIONS:**
Projection assumes illustrated rate of 5.5%, allocations of 20% in year 1 and 60% in subsequent years. Actual results may vary and are not guaranteed.

**🚀 NEXT STEPS:**
1. **Review the breakdown** - Does this coverage amount feel right for your situation?
2. **Ask questions** - I can explain any part of the calculation in more detail
3. **Explore options** - We can discuss different policy types and features
4. **Get professional advice** - Consider consulting with a licensed insurance professional

**💬 AVAILABLE ACTIONS:**
• **Ask Robo-Advisor** - Get more detailed explanations
• **Start Application** - Begin the application process
• **Start Over** - Recalculate with different inputs

**What would you like me to explain about this coverage amount or the different components?**"""
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating default response: {e}")
            return "Your calculation is complete! I've determined your life insurance needs. What would you like to know more about?"

    async def _generate_welcome_message(self, context: ConversationContext) -> str:
        """Generate a personalized welcome message"""
        try:
            prompt = self._build_welcome_prompt(context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"🧮 Error generating welcome message: {e}")
            return self._get_default_welcome_message()

    def _build_welcome_prompt(self, context: ConversationContext) -> str:
        """Build prompt for welcome message generation - chat-optimized"""
        return f"""Generate a friendly, conversational welcome message for starting a life insurance needs calculation.

**User Context:** {context.knowledge_level.value} level, current focus: {context.current_topic or 'Insurance Planning'}

**Requirements:**
- Keep it short and friendly (1-2 sentences max)
- Make it feel like talking to a real financial advisor
- Don't be overly formal or technical
- Encourage them to start

**Examples:**
- Beginner: "Great! Let's figure out how much life insurance you need. I'll ask you a few simple questions."
- Intermediate: "Perfect! I'll help you calculate your life insurance needs. This will only take a few minutes."
- Expert: "Excellent! Let's calculate your life insurance needs. I'll need some basic information from you."

**Generate a friendly welcome message:**
"""

    def _get_default_welcome_message(self) -> str:
        """Default welcome message if LLM generation fails - chat-optimized"""
        return "Great! Let's calculate your life insurance needs. I'll ask you a few questions to get started."

    async def _generate_contextual_question(self, question: Dict[str, Any], context: ConversationContext) -> str:
        """Generate a contextual question based on previous answers"""
        try:
            prompt = self._build_contextual_question_prompt(question, context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating contextual question: {e}")
            return self._get_simple_hint(question)

    def _build_contextual_question_prompt(self, question: Dict[str, Any], context: ConversationContext) -> str:
        """Build prompt for contextual question generation"""
        return f"""
        Generate a friendly, contextual question for a life insurance needs assessment.
        
        **Base Question:** {question['question']}
        **Question Type:** {question['type']}
        **User Context:** {context.knowledge_level.value} level, current focus: {context.current_topic or 'Insurance Planning'}
        
        **Requirements:**
        - Keep the question clear and friendly
        - Adapt to the user's knowledge level
        - Make it conversational and engaging
        - Include context from previous questions if relevant
        
        **Examples:**
        - Beginner: "To help us understand your life insurance needs better, what is your age?"
        - Intermediate: "For accurate coverage calculation, please tell me your current age."
        - Expert: "What is your age for the life insurance needs assessment?"
        
        **Generate a friendly, contextual version of the question:**
        """

    def _get_simple_hint(self, question: Dict[str, Any]) -> str:
        """Get a simple, helpful hint for each question - chat-optimized"""
        question_id = question["id"]
        
        # Simple, conversational hints
        hints = {
            "age": "Just enter your age as a number (e.g., 35).",
            "marital_status": "Choose: Single, Married, Divorced, or Widowed.",
            "dependents": "How many people depend on your income? (children, elderly parents, etc.)",
            "monthly_income": "Your monthly income before taxes (e.g., $5,000 or 5000).",
            "mortgage_balance": "Total debt including mortgage, loans, credit cards (e.g., $300,000).",
            "other_debts": "Your total assets (savings, investments, etc.) (e.g., $150,000).",
            "provide_education": "Do you want to provide for children's college education? (yes/no)",
            "individual_life": "Current individual life insurance amount (e.g., $100,000 or 0 if none).",
            "group_life": "Current group life insurance from work (e.g., $50,000 or 0 if none).",
            "cash_value_importance": "Do you want savings/cash value with your policy? (yes/no/unsure)",
            "permanent_coverage": "Do you want lifelong coverage or temporary? (yes/no/unsure)",
            "income_replacement_years": "How many years of income replacement? (5-20, default is 10)."
        }
        
        return hints.get(question_id, "")

    async def _handle_validation_failure(self, question: Dict[str, Any], answer: str, parsed_answer: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Handle validation failure with helpful guidance"""
        try:
            question_id = question["id"]
            error_message = parsed_answer.get("error", "Invalid answer")
            suggestion = parsed_answer.get("suggestion", "Please try again")
            
            # Generate a helpful response
            response = f"I couldn't understand your answer: '{answer}'. {error_message}\n\n"
            response += f"**Question:** {question['question']}\n"
            response += f"**Hint:** {suggestion}\n\n"
            
            # Add specific guidance based on question type
            if question["type"] == "number":
                response += "Please enter a number (e.g., 35 for age, 5000 for income)."
            elif question["type"] == "currency":
                response += "Please enter an amount (e.g., $5,000 or 5000)."
            elif question["type"] == "select":
                options = question.get("options", [])
                if options:
                    response += f"Please choose from: {', '.join(options)}"
            elif question["type"] == "boolean":
                response += "Please answer with yes or no."
            
            return {
                "status": "validation_failed",
                "message": response,
                "question": question["question"],
                "error": error_message,
                "suggestion": suggestion
            }
            
        except Exception as e:
            logger.error(f"🧮 Error handling validation failure: {e}")
            return {
                "status": "error",
                "message": "I encountered an error processing your answer. Please try again.",
                "error": str(e)
            }

    async def _retry_with_clarification(self, question: Dict[str, Any], original_answer: str, context: ConversationContext) -> Dict[str, Any]:
        """Retry parsing with additional clarification"""
        try:
            # Generate a more specific question
            clarification = await self._generate_clarification_request(question, original_answer)
            
            return {
                "status": "clarification_needed",
                "message": clarification,
                "question": question["question"],
                "original_answer": original_answer
            }
            
        except Exception as e:
            logger.error(f"🧮 Error in retry with clarification: {e}")
            return {
                "status": "error",
                "message": "Error generating clarification. Please try again.",
                "error": str(e)
            }

    def _get_alternative_input_methods(self, question: Dict[str, Any]) -> List[str]:
        """Get alternative ways to input the answer"""
        question_type = question.get("type", "text")
        
        alternatives = {
            "number": ["Just the number", "Use digits only", "No text needed"],
            "currency": ["Amount only", "Numbers only", "No $ or commas needed"],
            "select": ["Choose from the options", "Pick one answer", "Select from the list"],
            "boolean": ["Yes or no", "True or false", "1 or 0"],
            "text": ["Use simple words", "Be specific", "Keep it brief"]
        }
        
        return alternatives.get(question_type, ["Try a different format"])

    def _get_progressive_clarification(self, question: Dict[str, Any], attempt: int) -> str:
        """Get progressively more specific clarification based on attempt number"""
        question_id = question["id"]
        
        clarifications = {
            "age": [
                "Please enter just your age as a number.",
                "For example: 35 (not '35 years old' or 'I am 35')",
                "Just type the number: 35"
            ],
            "monthly_income": [
                "Please enter your monthly income as a number.",
                "For example: 5000 (not '$5,000' or 'five thousand')",
                "Just the number: 5000"
            ],
            "dependents": [
                "How many people depend on your income?",
                "For example: 2 (not 'two children' or 'I have 2 kids')",
                "Just the number: 2"
            ]
        }
        
        # Get the appropriate clarification level
        question_clarifications = clarifications.get(question_id, ["Please try again with a clearer answer."])
        attempt_index = min(attempt - 1, len(question_clarifications) - 1)
        
        return question_clarifications[attempt_index]

    async def _semantically_parse_answer(self, answer: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user answer using semantic understanding"""
        try:
            # Try direct parsing first
            direct_result = self._try_direct_parsing(answer, question)
            if direct_result["valid"]:
                return direct_result
            
            # Try semantic parsing
            semantic_result = await self._try_semantic_parsing(answer, question)
            if semantic_result["valid"]:
                return semantic_result
            
            # Try pattern matching
            pattern_result = self._try_pattern_matching(answer, question)
            if pattern_result["valid"]:
                return pattern_result
            
            # Try contextual inference
            contextual_result = await self._try_contextual_inference(answer, question)
            if contextual_result["valid"]:
                return contextual_result
            
            # All parsing methods failed
            logger.warning(f"🧮 All parsing methods failed for answer: '{answer}'")
            return {
                "valid": False,
                "value": None,
                "error": "Could not understand your answer",
                "suggestion": "Please provide a clear answer to the question"
            }
            
        except Exception as e:
            logger.error(f"🧮 Error in semantic parsing: {e}")
            return {
                "valid": False,
                "value": None,
                "error": "Error processing your answer",
                "suggestion": "Please try again"
            }

    def _try_direct_parsing(self, answer: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """Try to parse answer directly based on question type"""
        try:
            question_type = question.get("type", "text")
            question_id = question["id"]
            logger.info(f"🧮 Direct parsing - question type: {question_type}, question id: {question_id}, answer: '{answer}'")
            
            if question_type == "number":
                # Try to extract number
                numbers = re.findall(r'\d+', answer)
                if numbers:
                    value = int(numbers[0])
                    validation = question.get("validation", {})
                    
                    if "min" in validation and value < validation["min"]:
                        return {"valid": False, "value": None, "error": f"Value must be at least {validation['min']}"}
                    if "max" in validation and value > validation["max"]:
                        return {"valid": False, "value": None, "error": f"Value must be at most {validation['max']}"}
                    
                    return {"valid": True, "value": value, "parsed_from": answer}
            
            elif question_type == "select":
                # Try to match options
                options = question.get("options", [])
                answer_lower = answer.lower().strip()
                
                for option in options:
                    if answer_lower in option.lower() or option.lower() in answer_lower:
                        return {"valid": True, "value": option, "parsed_from": answer}
                
                return {"valid": False, "value": None, "error": f"Please choose from: {', '.join(options)}"}
            
            elif question_type == "boolean":
                # Try to parse yes/no
                answer_lower = answer.lower().strip()
                if answer_lower in ["yes", "y", "true", "1"]:
                    return {"valid": True, "value": True, "parsed_from": answer}
                elif answer_lower in ["no", "n", "false", "0"]:
                    return {"valid": True, "value": False, "parsed_from": answer}
                
                return {"valid": False, "value": None, "error": "Please answer with yes or no"}
            
            elif question_type == "currency":
                # Try to extract currency amount - more robust pattern
                # First try the standard pattern
                currency_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
                matches = re.findall(currency_pattern, answer)
                
                if not matches:
                    # Try a more flexible pattern for edge cases
                    flexible_pattern = r'\$?([\d,]+(?:\.\d+)?)'
                    matches = re.findall(flexible_pattern, answer)
                
                if matches:
                    # Clean up the matched value
                    value_str = matches[0].replace(',', '')
                    
                    # Handle cases where user might have typed extra zeros or made typos
                    # For example, "$2,000,0000" should be interpreted as "$2,000,000"
                    if len(value_str) > 6 and value_str.endswith('0'):
                        # If it's a large number ending with 0, try removing trailing zeros
                        # but only if it makes sense (e.g., 20000000 -> 2000000)
                        original_value = value_str
                        while len(value_str) > 6 and value_str.endswith('0'):
                            value_str = value_str[:-1]
                        
                        # If the cleaned value is reasonable, use it
                        if len(value_str) >= 6:  # At least 6 digits for large amounts
                            logger.info(f"🧮 Cleaned currency value from '{original_value}' to '{value_str}'")
                        else:
                            value_str = original_value  # Revert if we removed too many
                    
                    try:
                        value = float(value_str)
                        validation = question.get("validation", {})
                        
                        if "min" in validation and value < validation["min"]:
                            return {"valid": False, "value": None, "error": f"Amount must be at least ${validation['min']:,.2f}"}
                        if "max" in validation and value > validation["max"]:
                            return {"valid": False, "value": None, "error": f"Amount must be at most ${validation['max']:,.2f}"}
                        
                        logger.info(f"🧮 Currency parsing successful: {value}")
                        return {"valid": True, "value": value, "parsed_from": answer}
                    except ValueError:
                        # If float conversion fails, try to extract just the digits
                        digits_only = re.findall(r'\d', answer)
                        if digits_only:
                            # Reconstruct a reasonable number
                            value_str = ''.join(digits_only)
                            if len(value_str) > 6:
                                # For very long numbers, take the first 7 digits (reasonable for currency)
                                value_str = value_str[:7]
                            try:
                                value = float(value_str)
                                logger.info(f"🧮 Reconstructed currency value from digits: {value}")
                                return {"valid": True, "value": value, "parsed_from": answer}
                            except ValueError:
                                pass
                
                logger.warning(f"🧮 Currency parsing failed for answer: '{answer}'")
                return {"valid": False, "value": None, "error": "Please provide a valid amount (e.g., $5,000)"}
            
            logger.warning(f"🧮 Direct parsing failed - unsupported question type: {question_type}")
            return {"valid": False, "value": None, "error": "Unsupported question type"}
            
        except Exception as e:
            logger.error(f"🧮 Error in direct parsing: {e}")
            return {"valid": False, "value": None, "error": "Error parsing answer"}

    async def _try_semantic_parsing(self, answer: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """Try to parse answer using semantic understanding with LLM"""
        try:
            logger.info(f"🧮 Trying semantic parsing for answer: '{answer}' to question: {question.get('id', '')}")
            prompt = f"""
            Parse this user answer for a calculator question:
            
            Question: {question.get('question', '')}
            Question Type: {question.get('type', '')}
            Question ID: {question.get('id', '')}
            User Answer: {answer}
            
            Extract the relevant value based on the question type and format it appropriately.
            Return only the parsed value, nothing else.
            """
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            parsed_value = response.choices[0].message.content.strip()
            
            # Validate the parsed value
            validation_result = self._validate_parsed_value(parsed_value, question)
            if validation_result["valid"]:
                logger.info(f"🧮 Semantic parsing successful: {validation_result['value']}")
                return {"valid": True, "value": validation_result["value"], "parsed_from": answer}
            else:
                logger.warning(f"🧮 Semantic parsing validation failed: {validation_result['error']}")
                return validation_result
                
        except Exception as e:
            logger.error(f"🧮 Error in semantic parsing: {e}")
            return {"valid": False, "value": None, "error": "Error in semantic parsing"}

    def _try_pattern_matching(self, answer: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """Try to parse answer using pattern matching"""
        try:
            logger.info(f"🧮 Trying pattern matching for answer: '{answer}' to question type: {question.get('type', '')}")
            question_type = question.get("type", "text")
            
            if question_type == "number":
                # Look for numbers in various formats
                patterns = [
                    r'\b(\d+)\s*(?:years? old?|y\.?o\.?|age)?\b',  # age patterns
                    r'\b(\d+)\s*(?:children?|kids?|dependents?)\b',  # dependent patterns
                    r'\b(\d+)\b'  # general number
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, answer, re.IGNORECASE)
                    if match:
                        value = int(match.group(1))
                        return {"valid": True, "value": value, "parsed_from": answer}
            
            elif question_type == "currency":
                # Look for currency in various formats
                patterns = [
                    r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',
                    r'(\d+)\s*k\b',  # 50k = $50,000
                    r'(\d+)\s*m\b'   # 1m = $1,000,000
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, answer, re.IGNORECASE)
                    if match:
                        value_str = match.group(1)
                        if 'k' in answer.lower():
                            value = int(value_str) * 1000
                        elif 'm' in answer.lower():
                            value = int(value_str) * 1000000
                        else:
                            value = float(value_str.replace(',', ''))
                        
                        return {"valid": True, "value": value, "parsed_from": answer}
            
            logger.warning(f"🧮 Pattern matching failed for answer: '{answer}'")
            return {"valid": False, "value": None, "error": "Pattern matching failed"}
            
        except Exception as e:
            logger.error(f"🧮 Error in pattern matching: {e}")
            return {"valid": False, "value": None, "error": "Error in pattern matching"}

    async def _try_contextual_inference(self, answer: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """Try to infer answer from context using LLM"""
        try:
            logger.info(f"🧮 Trying contextual inference for answer: '{answer}' to question: {question.get('id', '')}")
            prompt = f"""
            Based on this user's answer, infer what they mean for this calculator question:
            
            Question: {question.get('question', '')}
            Question Type: {question.get('type', '')}
            User Answer: {answer}
            
            Consider the context and common ways people express this information.
            Return only the inferred value, nothing else.
            """
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            inferred_value = response.choices[0].message.content.strip()
            
            # Validate the inferred value
            validation_result = self._validate_parsed_value(inferred_value, question)
            if validation_result["valid"]:
                logger.info(f"🧮 Contextual inference successful: {validation_result['value']}")
                return {"valid": True, "value": validation_result["value"], "parsed_from": answer}
            else:
                logger.warning(f"🧮 Contextual inference validation failed: {validation_result['error']}")
                return validation_result
                
        except Exception as e:
            logger.error(f"🧮 Error in contextual inference: {e}")
            return {"valid": False, "value": None, "error": "Error in contextual inference"}

    def _validate_parsed_value(self, value: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a parsed value against question constraints"""
        try:
            logger.info(f"🧮 Validating parsed value: '{value}' for question type: {question.get('type', '')}")
            question_type = question.get("type", "text")
            validation = question.get("validation", {})
            
            if question_type == "number":
                try:
                    num_value = int(value)
                    if "min" in validation and num_value < validation["min"]:
                        return {"valid": False, "value": None, "error": f"Value must be at least {validation['min']}"}
                    if "max" in validation and num_value > validation["max"]:
                        return {"valid": False, "value": None, "error": f"Value must be at most {validation['max']}"}
                    return {"valid": True, "value": num_value}
                except ValueError:
                    return {"valid": False, "value": None, "error": "Invalid number format"}
            
            elif question_type == "currency":
                try:
                    # Remove currency symbols and commas
                    clean_value = value.replace('$', '').replace(',', '')
                    num_value = float(clean_value)
                    if "min" in validation and num_value < validation["min"]:
                        logger.warning(f"🧮 Currency validation failed - below minimum: {num_value} < {validation['min']}")
                        return {"valid": False, "value": None, "error": f"Amount must be at least ${validation['min']:,.2f}"}
                    if "max" in validation and num_value > validation["max"]:
                        logger.warning(f"🧮 Currency validation failed - above maximum: {num_value} > {validation['max']}")
                        return {"valid": False, "value": None, "error": f"Amount must be at most ${validation['max']:,.2f}"}
                    logger.info(f"🧮 Currency validation successful: {num_value}")
                    return {"valid": True, "value": num_value}
                except ValueError:
                    logger.warning(f"🧮 Currency validation failed - invalid format: '{value}'")
                    return {"valid": False, "value": None, "error": "Invalid currency format"}
            
            elif question_type == "select":
                options = question.get("options", [])
                if value in options:
                    logger.info(f"🧮 Select validation successful: {value}")
                    return {"valid": True, "value": value}
                else:
                    logger.warning(f"🧮 Select validation failed - '{value}' not in options: {options}")
                    return {"valid": False, "value": None, "error": f"Value must be one of: {', '.join(options)}"}
            
            elif question_type == "boolean":
                if value.lower() in ["true", "false", "yes", "no", "1", "0"]:
                    bool_value = value.lower() in ["true", "yes", "1"]
                    logger.info(f"🧮 Boolean validation successful: {bool_value}")
                    return {"valid": True, "value": bool_value}
                else:
                    logger.warning(f"🧮 Boolean validation failed - '{value}' not a valid boolean")
                    return {"valid": False, "value": None, "error": "Value must be true/false or yes/no"}
            
            logger.info(f"🧮 Validation successful for value: {value}")
            return {"valid": True, "value": value}
            
        except Exception as e:
            logger.error(f"🧮 Error validating parsed value: {e}")
            return {"valid": False, "value": None, "error": "Error validating value"}

    async def _generate_clarification_request(self, question: Dict[str, Any], original_answer: str) -> str:
        """Generate a helpful clarification request"""
        try:
            prompt = f"""
            Generate a helpful clarification request for this calculator question:
            
            Question: {question.get('question', '')}
            Question Type: {question.get('type', '')}
            User's Answer: {original_answer}
            
            Create a friendly, helpful message that:
            1. Acknowledges their attempt to answer
            2. Explains what we need more clearly
            3. Provides examples of acceptable formats
            4. Encourages them to try again
            
            Keep it conversational and helpful.
            """
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"🧮 Error generating clarification request: {e}")
            return f"I didn't quite understand your answer. Please provide a clear response to: {question.get('question', '')}"

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a calculator session"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"status": "not_found"}
            
            return {
                "status": session.get("status", "unknown"),
                "current_question": session.get("current_question_index", 0),
                "total_questions": len(self.standard_questions),
                "answers": session.get("answers", {}),
                "started_at": session.get("started_at"),
                "completed_at": session.get("completed_at")
            }
            
        except Exception as e:
            logger.error(f"🧮 Error getting session status: {e}")
            return {"status": "error", "error": str(e)}

    def reset_session(self, session_id: str) -> bool:
        """Reset a calculator session"""
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error resetting session: {e}")
            return False

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old calculator sessions"""
        try:
            current_time = datetime.utcnow()
            cleaned_count = 0
            
            for session_id, session in list(self.active_sessions.items()):
                if "started_at" in session:
                    started_time = datetime.fromisoformat(session["started_at"])
                    age_hours = (current_time - started_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        del self.active_sessions[session_id]
                        cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
            return 0

    def close(self):
        """Clean up resources"""
        try:
            self.active_sessions.clear()
            logger.info("QuickCalculator resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up QuickCalculator: {e}") 