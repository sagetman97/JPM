"""
Function-calling tools for Financial Advisor LangGraph system.
Based on AIE7 course patterns with @tool decorators and proper docstrings.
"""

from typing import Annotated, List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from config.settings import settings
import json
import pandas as pd


# Initialize embeddings
embeddings = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL)

# Vector store will be initialized in app.py when client is available
vector_store = None


@tool
def retrieve_life_insurance_knowledge(
    query: Annotated[str, "Query to search in life insurance knowledge base"]
) -> str:
    """
    Retrieve information from the life insurance knowledge base using RAG.
    Use this tool to answer questions about life insurance products, policies, and best practices.
    """
    try:
        if vector_store is None:
            return "Knowledge base not available. Please ensure the vector store is properly initialized."
        
        # Get relevant documents from vector store
        docs = vector_store.similarity_search(query, k=settings.TOP_K_RETRIEVAL)
        
        # Combine document content
        context = "\n\n".join([doc.page_content for doc in docs])
        
        if not context:
            return "I don't have specific information about that in my knowledge base."
        
        # Use LLM to generate a coherent response from the context
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.1)
        
        prompt = ChatPromptTemplate.from_template("""
You are a financial advisor assistant specializing in life insurance. 

Based on the following context from the knowledge base, provide a clear, professional answer to the user's question.

Context: {context}

Question: {question}

Provide a comprehensive, well-structured response that:
1. Directly answers the question
2. Uses information from the provided context
3. Is written in a professional, educational tone
4. Is organized and easy to understand
5. Includes relevant details and examples when appropriate

Response:""")
        
        chain = prompt | llm
        
        response = chain.invoke({
            "context": context,
            "question": query
        })
        
        return response.content
        
    except Exception as e:
        return f"Error retrieving information: {str(e)}"


@tool
def search_current_market_info(
    query: Annotated[str, "Query to search for current market information"]
) -> str:
    """
    Search for current market information, rates, and trends in life insurance.
    Use this tool to get up-to-date information about current rates, market conditions, and industry trends.
    """
    try:
        from tavily import TavilyClient
        from config.settings import settings
        
        if not settings.TAVILY_API_KEY:
            return "Tavily API key not configured. Cannot perform external search."
        
        # Initialize Tavily client
        tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # Enhance query for financial context
        enhanced_query = f"life insurance {query} current rates market conditions 2024 financial planning"
        
        print(f"🔍 **TAVILY SEARCH**")
        print(f"   Query: {enhanced_query}")
        
        # Perform search
        search_result = tavily_client.search(
            query=enhanced_query,
            search_depth="advanced",
            max_results=5
        )
        
        # Extract and format results
        results = search_result.get("results", [])
        
        if not results:
            return f"No current market information found for: {query}"
        
        # Format the results
        formatted_results = []
        for i, result in enumerate(results[:3], 1):  # Limit to top 3 results
            title = result.get("title", "No title")
            content = result.get("content", "No content")
            url = result.get("url", "")
            
            # Create a more structured format for the LLM to reference
            formatted_results.append(f"**Source {i}: {title}**\nURL: {url}\nContent: {content[:400]}...\n")
        
        # Combine results
        combined_content = "\n".join(formatted_results)
        
        # Use LLM to synthesize the search results
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.1)
        
        synthesis_prompt = ChatPromptTemplate.from_template("""
You are a financial advisor assistant. Based on the following search results about life insurance, provide a comprehensive, well-structured response to the user's query.

Search Results:
{search_results}

User Query: {user_query}

Please provide a response that:
1. Directly answers the user's question
2. Uses information from the search results
3. Is well-organized and professional
4. Includes relevant details and examples
5. Focuses on current market information and trends
6. Includes source citations throughout the response using [Source: Title] format
7. End with a "Sources:" section listing all sources used

Format your response with inline citations like this:
"According to [Source: Guardian], current rates for 30-year-old males..."

And end with:
Sources:
1. [Title] - [URL]
2. [Title] - [URL]
etc.

Response:""")
        
        chain = synthesis_prompt | llm
        
        response = chain.invoke({
            "search_results": combined_content,
            "user_query": query
        })
        
        # Ensure sources are included
        response_content = response.content
        
        # If sources aren't already included, add them
        if "Sources:" not in response_content:
            sources_section = "\n\n**Sources:**\n"
            for i, result in enumerate(results[:3], 1):
                title = result.get("title", "Unknown Source")
                url = result.get("url", "")
                sources_section += f"{i}. [{title}]({url})\n"
            
            response_content += sources_section
        
        return response_content
        
    except Exception as e:
        print(f"❌ **TAVILY SEARCH ERROR**: {str(e)}")
        return f"Error searching market information: {str(e)}"


@tool
def calculate_coverage_needs(
    income: Annotated[float, "Annual income"],
    dependents: Annotated[int, "Number of dependents"],
    age: Annotated[int, "Age of the insured"],
    debt: Annotated[float, "Total outstanding debt"],
    funeral_expenses: Annotated[float, "Estimated funeral and final expenses"],
    existing_coverage: Annotated[float, "Existing life insurance coverage"]
) -> str:
    """
    Calculate life insurance coverage needs using multiple methodologies.
    Use this tool to determine how much life insurance coverage is needed based on financial situation.
    """
    try:
        # Calculate expenses as 40% of income (standard rule of thumb)
        expenses = income * 0.4
        
        # Calculate education funding automatically ($52,000 per dependent)
        education_funding_per_child = 52000
        total_education_funding = dependents * education_funding_per_child
        
        # Multiple calculation methodologies
        income_replacement = income * 10  # 10x income rule
        expense_coverage = expenses * 15  # 15x expenses rule
        dependent_coverage = dependents * 100000  # $100k per dependent
        debt_coverage = debt * 1.1  # 110% of debt to account for interest
        education_coverage = total_education_funding
        final_expenses = funeral_expenses
        
        # Calculate total needed using comprehensive methodology
        # Base coverage: Income replacement OR expense coverage (whichever is higher)
        base_coverage = max(income_replacement, expense_coverage)
        
        # Add additional components
        total_needed = base_coverage + debt_coverage + education_coverage + final_expenses
        additional_needed = max(0, total_needed - existing_coverage)
        
        # Calculate monthly premium estimate (more realistic)
        if age < 40:
            # Younger individuals - consider permanent options
            base_rate = 0.0008  # $0.80 per $1000 coverage per month
            age_factor = 1 + (age - 30) * 0.02  # Age adjustment
        else:
            # Older individuals - term life is more cost-effective
            base_rate = 0.0012  # $1.20 per $1000 coverage per month
            age_factor = 1 + (age - 30) * 0.025  # Age adjustment
        
        monthly_premium = (additional_needed / 1000) * base_rate * age_factor
        
        # Determine policy type recommendation based on age, income, and financial situation
        if age < 35 and income > 150000:
            recommended_policy = "Index Universal Life (IUL)"
            policy_reasoning = "Young age with high income makes IUL ideal. Provides tax-deferred cash value growth, potential for tax-free distributions, and death benefit protection. Perfect for high-income earners seeking both protection and wealth accumulation."
        elif age < 40 and income > 100000:
            recommended_policy = "Variable Universal Life (VUL)"
            policy_reasoning = "Good age and income for VUL. Offers investment control with higher growth potential, tax advantages, and flexibility in premiums and death benefit."
        elif age < 45 and income > 75000:
            recommended_policy = "Term Life"
            policy_reasoning = "Optimal balance of cost and coverage. Term life provides maximum death benefit for minimum cost, ideal for protection-focused needs."
        elif age < 50:
            recommended_policy = "Term Life"
            policy_reasoning = "Most cost-effective option for your age group. Permanent policies become prohibitively expensive, making term life the practical choice."
        else:
            recommended_policy = "Term Life"
            policy_reasoning = "Most cost-effective option for your age and coverage needs. Permanent policies are too expensive at this age."
        
        # Add specific product recommendations based on income level
        if income > 200000:
            product_details = """
**Product-Specific Recommendations:**
- **Index Universal Life (IUL):** Best for high-income earners seeking tax advantages and cash value growth
- **Variable Universal Life (VUL):** Consider if you want investment control and higher growth potential
- **Whole Life:** Traditional option with guaranteed cash value growth
- **Term Life:** Pure protection at lowest cost"""
        elif income > 100000:
            product_details = """
**Product-Specific Recommendations:**
- **Universal Life (UL):** Good balance of flexibility and cash value growth
- **Index Universal Life (IUL):** Tax advantages with market-linked growth
- **Term Life:** Maximum coverage for minimum cost"""
        else:
            product_details = """
**Product-Specific Recommendations:**
- **Term Life:** Most cost-effective option for your income level
- **Simplified Issue Whole Life:** If you need permanent coverage and qualify"""
        
        return f"""
**Life Insurance Needs Analysis**

**Current Financial Situation:**
- Annual Income: ${income:,.2f}
- Estimated Annual Expenses: ${expenses:,.2f} (40% of income)
- Number of Dependents: {dependents}
- Age: {age}
- Total Debt: ${debt:,.2f}
- Education Funding Needs: ${total_education_funding:,.2f} (${education_funding_per_child:,.0f} per child)
- Funeral Expenses: ${funeral_expenses:,.2f}
- Existing Coverage: ${existing_coverage:,.2f}

**Coverage Analysis Breakdown:**
- **Base Coverage:** ${base_coverage:,.2f}
  *Income replacement (${income_replacement:,.0f}) or expense coverage (${expense_coverage:,.0f}), whichever is higher*
- **Debt Coverage:** ${debt_coverage:,.2f}
  *110% of debt to account for interest and fees*
- **Education Coverage:** ${education_coverage:,.2f}
  *${education_funding_per_child:,.0f} per child for college education*
- **Final Expenses:** ${final_expenses:,.2f}
  *Funeral and burial costs*

**Recommendation:**
- **Total Coverage Needed:** ${total_needed:,.2f}
- **Additional Coverage Needed:** ${additional_needed:,.2f}
- **Recommended Policy Type:** {recommended_policy}

**Why This Coverage Amount:**
This comprehensive analysis ensures your family's financial security by covering:
1. **Base Coverage:** ${base_coverage:,.0f} to maintain your family's lifestyle and expenses
2. **Debt Elimination:** ${debt_coverage:,.0f} to clear all outstanding obligations
3. **Education Funding:** ${education_coverage:,.0f} for your {dependents} dependent(s)
4. **Final Expenses:** ${final_expenses:,.0f} for funeral and burial costs

**Policy Recommendation Reasoning:**
{policy_reasoning}

{product_details}

**Next Steps:**
1. Compare quotes from multiple insurers
2. Consider riders for additional protection
3. Review coverage annually as your situation changes
4. Consult with a licensed insurance professional
        """
    except Exception as e:
        return f"Error calculating coverage needs: {str(e)}"


@tool
def analyze_portfolio_for_insurance(
    portfolio_data: Annotated[str, "Portfolio data in JSON format or CSV file path"]
) -> str:
    """
    Analyze client portfolio for life insurance integration.
    Use this tool to understand how life insurance fits into overall financial planning.
    """
    try:
        import pandas as pd
        import json
        
        # Check if portfolio_data is a JSON string or file path
        if portfolio_data.startswith('{'):
            # Parse JSON data
            data = json.loads(portfolio_data)
        else:
            # Try to read as CSV file
            try:
                df = pd.read_csv(portfolio_data)
                print(f"📊 **CSV DATA LOADED**")
                print(f"Columns: {list(df.columns)}")
                print(f"Rows: {len(df)}")
                
                # Convert DataFrame to dictionary for analysis
                data = {}
                
                # Extract key financial metrics
                if 'total_assets' in df.columns or 'Total Assets' in df.columns:
                    col = 'total_assets' if 'total_assets' in df.columns else 'Total Assets'
                    data['total_assets'] = df[col].sum()
                
                if 'liquid_assets' in df.columns or 'Liquid Assets' in df.columns:
                    col = 'liquid_assets' if 'liquid_assets' in df.columns else 'Liquid Assets'
                    data['liquid_assets'] = df[col].sum()
                
                if 'retirement_assets' in df.columns or 'Retirement Assets' in df.columns:
                    col = 'retirement_assets' if 'retirement_assets' in df.columns else 'Retirement Assets'
                    data['retirement_assets'] = df[col].sum()
                
                if 'debt' in df.columns or 'Debt' in df.columns:
                    col = 'debt' if 'debt' in df.columns else 'Debt'
                    data['debt'] = df[col].sum()
                
                # Calculate totals if individual columns don't exist
                if 'total_assets' not in data:
                    numeric_columns = df.select_dtypes(include=['number']).columns
                    data['total_assets'] = df[numeric_columns].sum().sum()
                
                # Add portfolio composition analysis
                data['portfolio_composition'] = {}
                for col in df.columns:
                    if df[col].dtype in ['int64', 'float64']:
                        data['portfolio_composition'][col] = df[col].sum()
                
            except Exception as e:
                return f"Error reading CSV file: {str(e)}"
        
        # Use LLM for comprehensive portfolio analysis
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        analysis_prompt = ChatPromptTemplate.from_template("""
You are a financial advisor specializing in portfolio analysis and life insurance integration. Analyze the provided portfolio data and provide comprehensive recommendations.

**Portfolio Data:**
{portfolio_data}

**Analysis Requirements:**
1. **Portfolio Assessment**: Analyze the current portfolio composition, risk level, and diversification
2. **Life Insurance Integration**: Recommend how life insurance can complement the portfolio
3. **Product Recommendations**: Suggest specific life insurance products (Term, Whole Life, Universal Life, IUL, VUL) based on the portfolio
4. **Strategic Benefits**: Explain how life insurance provides portfolio diversification and tax advantages

**Provide a comprehensive analysis covering:**
- Current portfolio strengths and weaknesses
- Risk assessment and diversification analysis
- Life insurance product recommendations with reasoning
- How life insurance can enhance the overall financial strategy
- Specific product types and why they're suitable

**Focus on:**
- Cash value life insurance benefits for portfolio diversification
- Tax advantages of permanent life insurance
- Risk management through life insurance
- Wealth accumulation strategies

Return a detailed, professional analysis that helps the client understand how life insurance fits into their financial plan.
""")
        
        try:
            # Use LLM for analysis
            llm = ChatOpenAI(model="gpt-4", temperature=0.1)
            analysis_chain = analysis_prompt | llm
            
            result = analysis_chain.invoke({"portfolio_data": json.dumps(data, indent=2)})
            
            return result.content
            
        except Exception as e:
            print(f"❌ **LLM ANALYSIS ERROR:** {str(e)}")
            # Fallback to basic analysis
            return f"Error performing portfolio analysis: {str(e)}"
        
    except Exception as e:
        return f"Error analyzing portfolio: {str(e)}"


@tool
def assess_confidence_and_escalate(
    response: Annotated[str, "Current response to evaluate"],
    query: Annotated[str, "Original user query"]
) -> str:
    """
    Assess confidence in current response and determine if external search is needed.
    Use this tool to evaluate response quality and escalate to external search if needed.
    """
    try:
        # Simple confidence assessment
        response_length = len(response)
        has_uncertainty = any(word in response.lower() for word in ["i don't know", "not sure", "may vary", "consult"])
        
        if response_length < 200 or has_uncertainty:
            return "LOW_CONFIDENCE - External search recommended"
        else:
            return "HIGH_CONFIDENCE - Response is sufficient"
    except Exception as e:
        return f"Error assessing confidence: {str(e)}"


def initialize_vector_store(client):
    """
    Initialize the vector store with the provided client.
    """
    global vector_store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        embedding=embeddings,
        vector_name="text"  # Match the existing collection's vector name
    ) 