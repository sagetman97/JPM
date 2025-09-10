"""
Main Graph Builder for Financial Advisor LangGraph system.
Based on AIE7 course patterns for hierarchical agent teams.
"""

import functools
from typing import Any, Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from .state import FinancialAdvisorState
from .supervisors import create_main_supervisor
import json


def greeting_node(state: FinancialAdvisorState) -> Dict[str, Any]:
    """
    Handle simple greetings following AIE7 course patterns.
    """
    greeting_responses = [
        "Hello! I'm your Financial Advisor Life Insurance Assistant. I'm here to help you with life insurance questions, coverage calculations, portfolio analysis, and more. How can I assist you today?",
        "Hi there! I'm ready to help you with life insurance and financial planning questions. What would you like to know?",
        "Hello! I'm your AI assistant specializing in life insurance and financial planning. I can help you calculate coverage needs, analyze portfolios, and provide comprehensive information. What can I help you with?"
    ]
    
    import random
    response = random.choice(greeting_responses)
    
    return {
        "messages": [AIMessage(content=response)],
        "final_response": response
    }


def create_main_graph(llm: ChatOpenAI) -> Any:
    """
    Create the main LangGraph with hierarchical team structure.
    Based on AIE7 course patterns for multi-agent systems.
    """
    
    # Import here to avoid circular imports
    from ..teams.research_team import create_research_chain
    from ..teams.analysis_team import create_analysis_chain
    
    # Create team chains
    research_chain = create_research_chain(llm)
    analysis_chain = create_analysis_chain(llm)
    
    # Create main supervisor
    main_supervisor = create_main_supervisor(llm)
    
    # Build the main graph
    main_graph = StateGraph(FinancialAdvisorState)
    
    # Add nodes
    main_graph.add_node("main_supervisor", main_supervisor)
    main_graph.add_node("greeting", greeting_node)
    main_graph.add_node("research_team", research_chain)
    main_graph.add_node("analysis_team", analysis_chain)
    
    # Add edges from START
    main_graph.add_edge(START, "main_supervisor")
    
    # Add conditional edges from main supervisor
    main_graph.add_conditional_edges(
        "main_supervisor",
        lambda x: x["next"],
        {
            "RESEARCH_TEAM": "research_team",
            "ANALYSIS_TEAM": "analysis_team",
            "GREETING": "greeting",
            "FINISH": END
        }
    )
    
    # Add edges back to main supervisor from teams
    main_graph.add_edge("research_team", "main_supervisor")
    main_graph.add_edge("analysis_team", "main_supervisor")
    main_graph.add_edge("greeting", "main_supervisor")
    
    return main_graph.compile()


def create_financial_advisor_chain(llm: ChatOpenAI) -> Any:
    """
    Create the complete financial advisor chain for Chainlit integration.
    Based on AIE7 course patterns for chain integration.
    """
    
    def enter_chain(message: str):
        """Enter the main graph with a user message."""
        return {
            "messages": [HumanMessage(content=message)],
            "team_members": ["RESEARCH_TEAM", "ANALYSIS_TEAM"],
            "next": "",
            "session_context": {},
            "uploaded_files": [],
            "current_team": "MAIN",
            "query": message,
            "final_response": None
        }
    
    main_graph = create_main_graph(llm)
    financial_advisor_chain = enter_chain | main_graph
    
    return financial_advisor_chain


def process_query_with_langgraph(llm: ChatOpenAI, query: str, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process a user query through the LangGraph system.
    Based on AIE7 course patterns for query processing.
    """
    
    print(f"\n🔍 **LANGGRAPH PROCESSING START**")
    print(f"📝 Query: {query}")
    print(f"📊 Session Context: {session_context}")
    
    try:
        # Check if we're waiting for calculator data FIRST
        if session_context.get("waiting_for_calculator_data"):
            print(f"📊 **EXTRACTING CALCULATOR DATA**")
            
            # Check if user is trying to ask a different question
            if any(word in query.lower() for word in ["what is", "explain", "tell me about", "how does", "rag", "research", "search", "portfolio", "upload"]) and not any(word in query.lower() for word in ["income:", "expenses:", "dependents:", "age:", "debt:", "education", "funeral", "existing", "coverage:", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."]):
                print(f"🔄 **CLEARING CALCULATOR STATE - NEW QUESTION DETECTED**")
                # Clear calculator state and route to appropriate agent
                session_context.pop("calculator_data", None)
                session_context.pop("waiting_for_calculator_data", None)
                # Continue with normal routing below
            else:
                # Extract financial data from user response using LLM
                import re
                import json
                
                # Use LLM to extract structured data
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import ChatPromptTemplate
                
                extraction_prompt = ChatPromptTemplate.from_template("""
You are a financial data extraction specialist. Extract the following financial information from the user's response and return it as a JSON object.

**Required fields to extract:**
- income: Annual income (float)
- dependents: Number of dependents (integer)
- age: Age (integer)
- debt: Total outstanding debt (float)
- funeral_expenses: Funeral expenses (float)
- existing_coverage: Existing life insurance coverage (float)

**User Response:**
{user_response}

**Instructions:**
1. Look for numbers that match each field
2. Convert all amounts to numbers (remove $ and commas)
3. If a field is not found, set it to 0
4. Return ONLY a valid JSON object with these exact field names
5. Do not include any explanations or additional text

**Example output:**
{{"income": 75000, "dependents": 2, "age": 35, "debt": 100000, "funeral_expenses": 15000, "existing_coverage": 0}}
""")
                
                try:
                    # Use LLM to extract data
                    llm = ChatOpenAI(model="gpt-4", temperature=0)
                    extraction_chain = extraction_prompt | llm
                    
                    result = extraction_chain.invoke({"user_response": query})
                    
                    # Parse the JSON response
                    extracted_data = json.loads(result.content)
                    
                    print(f"📊 **LLM EXTRACTED DATA:** {extracted_data}")
                    
                    # Update calculator data with extracted values
                    calculator_data = session_context.get("calculator_data", {})
                    calculator_data.update(extracted_data)
                    
                except Exception as e:
                    print(f"❌ **LLM EXTRACTION ERROR:** {str(e)}")
                    # Fallback to regex if LLM fails
                    calculator_data = session_context.get("calculator_data", {})
                    
                    # Helper function to safely convert string to float
                    def safe_float_convert(num_str):
                        try:
                            return float(num_str.replace(",", ""))
                        except (ValueError, AttributeError):
                            return 0.0
                    
                    def safe_int_convert(num_str):
                        try:
                            return int(float(num_str.replace(",", "")))
                        except (ValueError, AttributeError):
                            return 0
                    
                    # Extract numbers and their context
                    numbers = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', query)
                    words = query.lower().split()
                    
                    # Check if this looks like structured calculator data (with labels)
                    if any(word in query.lower() for word in ["income:", "dependents:", "age:", "debt:", "funeral", "existing", "coverage:"]):
                        print(f"📊 **DETECTED STRUCTURED CALCULATOR DATA**")
                        
                        # Extract income
                        if "income:" in query.lower():
                            income_match = re.search(r'income:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', query.lower())
                            if income_match:
                                calculator_data["income"] = safe_float_convert(income_match.group(1))
                        
                        # Extract dependents
                        if "dependents:" in query.lower():
                            dependents_match = re.search(r'dependents:\s*(\d+)', query.lower())
                            if dependents_match:
                                calculator_data["dependents"] = safe_int_convert(dependents_match.group(1))
                        
                        # Extract age
                        if "age:" in query.lower():
                            age_match = re.search(r'age:\s*(\d+)', query.lower())
                            if age_match:
                                calculator_data["age"] = safe_int_convert(age_match.group(1))
                        
                        # Extract debt
                        if "debt:" in query.lower():
                            debt_match = re.search(r'debt:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', query.lower())
                            if debt_match:
                                calculator_data["debt"] = safe_float_convert(debt_match.group(1))
                        
                        # Extract funeral expenses
                        if "funeral" in query.lower():
                            funeral_match = re.search(r'funeral.*?(\d+(?:,\d{3})*(?:\.\d{2})?)', query.lower())
                            if funeral_match:
                                calculator_data["funeral_expenses"] = safe_float_convert(funeral_match.group(1))
                        
                        # Extract existing coverage
                        if "existing" in query.lower() or "coverage:" in query.lower():
                            coverage_match = re.search(r'(?:existing|coverage).*?(\d+(?:,\d{3})*(?:\.\d{2})?)', query.lower())
                            if coverage_match:
                                calculator_data["existing_coverage"] = safe_float_convert(coverage_match.group(1))
                    
                    else:
                        # Original keyword-based extraction
                        # Extract income
                        if any(word in words for word in ["income", "salary", "earn"]) and len(numbers) > 0:
                            calculator_data["income"] = safe_float_convert(numbers[0])
                        
                        # Extract dependents
                        if any(word in words for word in ["dependent", "child", "children", "kid"]) and len(numbers) > 0:
                            calculator_data["dependents"] = safe_int_convert(numbers[0])
                        
                        # Extract age
                        if any(word in words for word in ["age", "old"]) and len(numbers) > 0:
                            calculator_data["age"] = safe_int_convert(numbers[0])
                        
                        # Extract debt
                        if any(word in words for word in ["debt", "loan", "mortgage"]) and len(numbers) > 0:
                            calculator_data["debt"] = safe_float_convert(numbers[0])
                        
                        # Extract funeral expenses
                        if any(word in words for word in ["funeral", "burial"]) and len(numbers) > 0:
                            calculator_data["funeral_expenses"] = safe_float_convert(numbers[0])
                        
                        # Extract existing coverage
                        if any(word in words for word in ["existing", "current", "already"]) and len(numbers) > 0:
                            calculator_data["existing_coverage"] = safe_float_convert(numbers[0])
                        
                        # If no specific keywords found, try to map numbers to fields based on order
                        if len(numbers) >= 6 and not any(key in calculator_data for key in ["income", "dependents", "age", "debt", "funeral_expenses", "existing_coverage"]):
                            # Map numbers to fields based on the order they were requested
                            try:
                                calculator_data["income"] = safe_float_convert(numbers[0])
                                calculator_data["dependents"] = safe_int_convert(numbers[1])
                                calculator_data["age"] = safe_int_convert(numbers[2])
                                calculator_data["debt"] = safe_float_convert(numbers[3])
                                calculator_data["funeral_expenses"] = safe_float_convert(numbers[4])
                                calculator_data["existing_coverage"] = safe_float_convert(numbers[5])
                            except (IndexError, ValueError):
                                pass
                
                # Update session context
                session_context["calculator_data"] = calculator_data
                
                # Check if we have enough data
                required_fields = ["income", "dependents", "age", "debt", "funeral_expenses", "existing_coverage"]
                missing_fields = [field for field in required_fields if field not in calculator_data]
                
                if missing_fields:
                    response = f"""**Data Collection Progress**

I've extracted the following information:
{chr(10).join([f"- {field.replace('_', ' ').title()}: {calculator_data.get(field, 'Not provided')}" for field in required_fields])}

**Still needed:**
{chr(10).join([f"- {field.replace('_', ' ').title()}" for field in missing_fields])}

Please provide the missing information to complete your life insurance needs analysis."""
                else:
                    # We have all the data, perform calculation
                    print(f"🧮 **PERFORMING CALCULATION WITH USER DATA**")
                    from agents.teams.tools import calculate_coverage_needs
                    
                    result = calculate_coverage_needs.invoke({
                        "income": calculator_data["income"],
                        "dependents": calculator_data["dependents"],
                        "age": calculator_data["age"],
                        "debt": calculator_data["debt"],
                        "funeral_expenses": calculator_data["funeral_expenses"],
                        "existing_coverage": calculator_data["existing_coverage"],
                        "policy_type": "term" # Automatically recommend term life insurance
                    })
                    
                    response = f"**Calculator Agent Response:**\n\n{result}"
                    
                    # Clear the calculator data after calculation
                    session_context.pop("calculator_data", None)
                    session_context.pop("waiting_for_calculator_data", None)
                
                return {
                    "response": response,
                    "metadata": {
                        "agent_type": "CALCULATOR_DATA_COLLECTION",
                        "teams_used": "CALCULATOR_AGENT",
                        "session_context": session_context,
                        "confidence": 0.8
                    }
                }
        
        # Check if we're waiting for portfolio context
        if session_context.get("waiting_for_portfolio_context"):
            print(f"📊 **EXTRACTING PORTFOLIO CONTEXT DATA**")
            
            # Check if user is trying to ask a different question
            if any(word in query.lower() for word in ["what is", "explain", "tell me about", "how does", "rag", "research", "search", "calculate", "how much"]):
                print(f"🔄 **CLEARING PORTFOLIO STATE - NEW QUESTION DETECTED**")
                # Clear portfolio state and route to appropriate agent
                session_context.pop("portfolio_context", None)
                session_context.pop("waiting_for_portfolio_context", None)
                # Continue with normal routing below
            else:
                # Extract portfolio context data from user response
                import re
            
                # Extract numbers and their context
                numbers = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', query)
                words = query.lower().split()
            
                portfolio_context = session_context.get("portfolio_context", {})
            
                # Extract income
                if any(word in words for word in ["income", "salary", "earn"]) and len(numbers) > 0:
                    portfolio_context["income"] = safe_float_convert(numbers[0])
                
                # Extract dependents
                if any(word in words for word in ["dependent", "child", "children", "kid"]) and len(numbers) > 0:
                    portfolio_context["dependents"] = safe_int_convert(numbers[0])
                
                # Extract age
                if any(word in words for word in ["age", "old"]) and len(numbers) > 0:
                    portfolio_context["age"] = safe_int_convert(numbers[0])
                
                # Extract risk tolerance
                if any(word in words for word in ["conservative", "moderate", "aggressive"]):
                    if "conservative" in words:
                        portfolio_context["risk_tolerance"] = "conservative"
                    elif "moderate" in words:
                        portfolio_context["risk_tolerance"] = "moderate"
                    elif "aggressive" in words:
                        portfolio_context["risk_tolerance"] = "aggressive"
                
                # Extract investment goals
                if any(word in words for word in ["retirement", "education", "wealth", "building"]):
                    if "retirement" in words:
                        portfolio_context["investment_goals"] = "retirement"
                    elif "education" in words:
                        portfolio_context["investment_goals"] = "children's education"
                    elif "wealth" in words or "building" in words:
                        portfolio_context["investment_goals"] = "wealth building"
                
                # Extract current insurance
                if any(word in words for word in ["current", "existing", "insurance"]) and len(numbers) > 0:
                    portfolio_context["current_insurance"] = safe_float_convert(numbers[0])
                
                # If no specific keywords found, try to map numbers to fields based on order
                if len(numbers) >= 6 and not any(key in portfolio_context for key in ["income", "dependents", "age", "risk_tolerance", "investment_goals", "current_insurance"]):
                    # Map numbers to fields based on the order they were requested
                    try:
                        portfolio_context["income"] = safe_float_convert(numbers[0])
                        portfolio_context["dependents"] = safe_int_convert(numbers[1])
                        portfolio_context["age"] = safe_int_convert(numbers[2])
                        portfolio_context["risk_tolerance"] = "moderate"  # Default
                        portfolio_context["investment_goals"] = "retirement"  # Default
                        portfolio_context["current_insurance"] = safe_float_convert(numbers[3]) if len(numbers) > 3 else 0
                    except (IndexError, ValueError):
                        pass
                
                # Update session context
                session_context["portfolio_context"] = portfolio_context
                
                # Check if we have enough data
                required_fields = ["income", "dependents", "age", "risk_tolerance", "investment_goals", "current_insurance"]
                missing_fields = [field for field in required_fields if field not in portfolio_context]
                
                if missing_fields:
                    response = f"""**Portfolio Context Collection Progress**

I've extracted the following information:
{chr(10).join([f"- {field.replace('_', ' ').title()}: {portfolio_context.get(field, 'Not provided')}" for field in required_fields])}

**Still needed:**
{chr(10).join([f"- {field.replace('_', ' ').title()}" for field in missing_fields])}

Please provide the missing information to complete your portfolio analysis."""
                else:
                    # We have all the data, perform portfolio analysis
                    print(f"📊 **PROCESSING PORTFOLIO WITH CONTEXT**")
                    from agents.teams.tools import analyze_portfolio_for_insurance
                    
                    # Get uploaded files
                    uploaded_files = session_context.get("uploaded_files", [])
                    file_path = uploaded_files[0].get("path", "") if uploaded_files else ""
                    
                    if file_path and file_path.endswith('.csv'):
                        result = analyze_portfolio_for_insurance.invoke({
                            "portfolio_data": file_path
                        })
                        
                        # Add portfolio context to the analysis
                        income = portfolio_context["income"]
                        dependents = portfolio_context["dependents"]
                        age = portfolio_context["age"]
                        risk_tolerance = portfolio_context["risk_tolerance"]
                        investment_goals = portfolio_context["investment_goals"]
                        current_insurance = portfolio_context["current_insurance"]
                        
                        enhanced_result = f"""{result}

**Personal Context Integration:**
- Annual Income: ${income:,.2f}
- Dependents: {dependents}
- Age: {age}
- Risk Tolerance: {risk_tolerance.title()}
- Investment Goals: {investment_goals.title()}
- Current Life Insurance: ${current_insurance:,.2f}

**Recommendations Based on Your Profile:**
Based on your {risk_tolerance} risk tolerance and {investment_goals} goals, I recommend focusing on term life insurance to protect your family while allowing your investment portfolio to grow. This approach aligns with your financial strategy and provides the coverage you need without compromising your investment returns."""
                        
                        response = f"**Portfolio Agent Response:**\n\n{enhanced_result}"
                    else:
                        response = "Error: No CSV file found for portfolio analysis."
                    
                    # Clear the portfolio context after analysis
                    session_context.pop("portfolio_context", None)
                    session_context.pop("waiting_for_portfolio_context", None)
                
                return {
                    "response": response,
                    "metadata": {
                        "agent_type": "PORTFOLIO_CONTEXT_COLLECTION",
                        "teams_used": "PORTFOLIO_AGENT",
                        "session_context": session_context,
                        "confidence": 0.8
                    }
                }
        
        # Simple keyword-based routing for now
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["calculate", "how much", "coverage amount", "needs analysis", "policy type", "term vs whole", "coverage needs"]):
            print(f"➡️  ROUTING TO: CALCULATOR_AGENT")
            from agents.teams.tools import calculate_coverage_needs
            
            # Extract financial data from query using LLM
            extraction_prompt = f"""
            Extract financial information from this query: "{query}"
            
            Return a JSON object with these fields (use 0 if not mentioned):
            {{
                "income": float,
                "dependents": int,
                "age": int,
                "debt": float,
                "funeral_expenses": float,
                "existing_coverage": float
            }}
            
            Only return the JSON object, nothing else.
            """
            
            extraction_result = llm.invoke(extraction_prompt)
            
            try:
                import json
                import re
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', extraction_result.content, re.DOTALL)
                if json_match:
                    financial_data = json.loads(json_match.group())
                else:
                    # Fallback to default values
                    financial_data = {
                        "income": 75000,
                        "dependents": 2,
                        "age": 35,
                        "debt": 150000,
                        "funeral_expenses": 10000,
                        "existing_coverage": 0
                    }
                
                # Check if we have meaningful data (not all zeros)
                has_meaningful_data = any([
                    financial_data.get("income", 0) > 0,
                    financial_data.get("dependents", 0) > 0,
                    financial_data.get("age", 0) > 0,
                    financial_data.get("debt", 0) > 0,
                    financial_data.get("funeral_expenses", 0) > 0
                ])
                
                # Also check if the query is asking for help rather than providing data
                is_help_request = any(word in query_lower for word in ["help", "how", "what", "calculate", "need", "should", "recommend"])
                
                if has_meaningful_data and not is_help_request:
                    print(f"📊 **CALCULATING WITH EXTRACTED DATA**")
                    # Calculate coverage needs
                    result = calculate_coverage_needs.invoke(financial_data)
                    
                    response = f"**Calculator Agent Response:**\n\n{result}"
                else:
                    print(f"📋 **COLLECTING FINANCIAL DATA**")
                    # Ask for financial information
                    response = """**Life Insurance Needs Calculator**

I'll help you calculate your life insurance coverage needs. To provide an accurate analysis, I need some information about your financial situation.

Please provide the following details:

1. **Annual Income:** (e.g., $75,000)
2. **Number of Dependents:** (e.g., 2)
3. **Your Age:** (e.g., 35)
4. **Total Outstanding Debt:** (e.g., $100,000)
5. **Funeral Expenses:** (e.g., $15,000)
6. **Existing Life Insurance Coverage:** (e.g., $0)

You can provide this information in any format - I'll extract the relevant details and recommend the best policy type for your situation."""
                    
                    # Store that we're waiting for calculator data
                    session_context["waiting_for_calculator_data"] = True
                    session_context["calculator_data"] = {}
                
            except Exception as e:
                response = f"**Calculator Agent Response:**\n\nI encountered an error while calculating your coverage needs: {str(e)}\n\nPlease provide your financial information in a clear format."
            
            return {
                "response": response,
                "metadata": {
                    "agent_type": "CALCULATOR_ANALYSIS",
                    "teams_used": "CALCULATOR_AGENT",
                    "session_context": session_context,
                    "confidence": 0.8
                }
            }
            
        # Research/External search detection - current market info, rates, trends
        elif any(word in query_lower for word in ["current rates", "market conditions", "specific company", "latest", "recent changes", "current term", "market trends", "2024", "this year", "now", "today", "current", "live", "real-time"]):
            print(f"➡️  ROUTING TO: SEARCH_AGENT")
            from agents.teams.tools import search_current_market_info
            
            # Perform external search
            result = search_current_market_info.invoke({
                "query": query
            })
            
            response = f"**Search Agent Response:**\n\n{result}"
            
            return {
                "response": response,
                "metadata": {
                    "agent_type": "SEARCH_ANALYSIS",
                    "teams_used": "SEARCH_AGENT",
                    "session_context": session_context,
                    "confidence": 0.8
                }
            }
            
        else:
            print(f"➡️  ROUTING TO: RAG_AGENT")
            # Test the RAG tool directly
            from agents.teams.tools import retrieve_life_insurance_knowledge
            
            # Get RAG response
            rag_response = retrieve_life_insurance_knowledge.invoke({"query": query})
            
            # Create a simple response
            response = f"**RAG Agent Response:**\n\n{rag_response}"
        
        print(f"✅ **RESPONSE GENERATED**")
        print(f"📝 Response length: {len(response)} characters")
        
        return {
            "response": response,
            "metadata": {
                "agent_type": "LANGGRAPH_SIMPLIFIED",
                "teams_used": "MULTI_AGENT",
                "session_context": session_context or {},
                "confidence": 0.8
            }
        }
        
    except Exception as e:
        print(f"❌ **ERROR**: {str(e)}")
        return {
            "response": f"I encountered an error while processing your query: {str(e)}",
            "metadata": {
                "agent_type": "ERROR",
                "error": str(e)
            }
        } 