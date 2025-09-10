"""
Main Chainlit application for the Financial Advisor Life Insurance Assistant.
Based on patterns from AIE7 course materials.
"""

import os
import uuid
import tempfile
from typing import List, Dict, Any
import chainlit as cl
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from qdrant_client import QdrantClient
from config.settings import settings
from agents.rag_agent import rag_agent
from agents.orchestrator import MultiAgentOrchestrator
from utils.file_processing import (
    process_uploaded_file, 
    validate_file_upload,
    extract_financial_data_from_excel,
    extract_portfolio_summary,
    create_session_document_collection
)
from utils.confidence import should_use_external_search


# Initialize Qdrant client
qdrant_client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT
)

# Initialize vector store with Qdrant client
from langchain_qdrant import QdrantVectorStore
rag_agent.vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name=settings.QDRANT_COLLECTION_NAME,
    embedding=rag_agent.embeddings,
    vector_name="text"
)

# Initialize Multi-Agent Orchestrator
orchestrator = MultiAgentOrchestrator(
    llm=ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.TEMPERATURE,
        max_tokens=settings.MAX_TOKENS
    ),
    rag_agent=rag_agent,
    tavily_api_key=settings.TAVILY_API_KEY
)


@cl.on_chat_start
async def start():
    """
    Initialize the chat session.
    Based on patterns from AIE7 course materials.
    """
    # Generate session ID
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)
    
    # Initialize session state
    cl.user_session.set("uploaded_files", [])
    cl.user_session.set("portfolio_data", {})
    
    # Welcome message
    await cl.Message(
        content="""👋 Welcome to the Financial Advisor Life Insurance Assistant!

I'm your AI-powered multi-agent system designed to help you confidently recommend life insurance products to your clients. I have specialized agents for:

🧠 **Query Router**: Intelligently routes your questions to the right specialist
🔍 **RAG Agent**: Access comprehensive life insurance knowledge base
📚 **Research Agent**: Get current market information and external data
🧮 **Calculator Agent**: Interactive life insurance needs analysis
📊 **Portfolio Agent**: Analyze client portfolios for insurance integration

**What I can do:**
• Answer questions about life insurance products and best practices
• Calculate coverage needs using multiple methodologies
• Analyze uploaded portfolios for personalized recommendations
• Research current market conditions and rates
• Provide confidence-based responses with external search when needed

**How to get started:**
1. Ask any question about life insurance or financial planning
2. Upload client portfolios (Excel, CSV, PDF) for analysis
3. Use natural language for calculator requests
4. Get comprehensive recommendations combining multiple perspectives

**Important**: I provide educational information to help you serve your clients better. Always consult with licensed professionals for specific advice.

What would you like to know about life insurance today?""",
        author="Assistant"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """
    Handle incoming messages using the Multi-Agent Orchestrator.
    Based on patterns from AIE7 course materials.
    """
    session_id = cl.user_session.get("session_id")
    user_message = message.content
    
    # Get session context
    session_context = {
        "session_id": session_id,
        "uploaded_files": cl.user_session.get("uploaded_files", []),
        "portfolio_data": cl.user_session.get("portfolio_data", {}),
        "client_info": cl.user_session.get("client_info", {})
    }
    
    # Send thinking message
    await cl.Message(
        content="🤔 Analyzing your request and routing to the appropriate specialist...",
        author="Assistant"
    ).send()
    
    # Process query through Multi-Agent Orchestrator
    try:
        result = orchestrator.process_query(user_message, session_context)
        
        # Update session context with any new information
        if result.get("metadata", {}).get("session_context"):
            cl.user_session.set("client_info", result["metadata"]["session_context"].get("client_info", {}))
        
        # Send response
        await cl.Message(
            content=result["response"],
            author="Assistant"
        ).send()
        
        # Show agent information if multiple agents were used
        metadata = result.get("metadata", {})
        if metadata.get("agents_used") and len(metadata["agents_used"]) > 1:
            agents_text = f"**Agents Used:** {', '.join(metadata['agents_used'])}"
            await cl.Message(
                content=agents_text,
                author="System"
            ).send()
        
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            await cl.Message(
                content="⚠️ **Rate Limit Reached**\n\nI'm experiencing high demand right now. Please wait a moment and try your question again.",
                author="Assistant"
            ).send()
        elif "timeout" in error_msg.lower():
            await cl.Message(
                content="⏱️ **Request Timeout**\n\nYour request is taking longer than expected. Please try again with a simpler question.",
                author="Assistant"
            ).send()
        else:
            await cl.Message(
                content=f"❌ **Error Processing Request**\n\nI encountered an error: {error_msg}\n\nPlease try rephrasing your question or contact support if the issue persists.",
                author="Assistant"
            ).send()





# @cl.on_file
# async def handle_file_upload(file: cl.File):
#     """
#     Handle file uploads using the Multi-Agent Orchestrator.
#     Based on patterns from AIE7 course materials.
#     """
#     session_id = cl.user_session.get("session_id")
#     
#     try:
#         # Validate file
#         if not validate_file_upload(file.path):
#             await cl.Message(
#                 content="❌ **File Upload Error**\n\nPlease ensure your file:\n• Is under 50MB\n• Is in a supported format (PDF, Excel, CSV, Word, TXT)\n• Contains valid financial data",
#                 author="Assistant"
#             ).send()
#             return
#         
#         # Process file
#         await cl.Message(
#             content=f"📁 Processing {file.name}...",
#             author="Assistant"
#         ).send()
#         
#         # Extract documents from file
#         documents = process_uploaded_file(file.path, session_id)
#         
#         # Add to session documents
#         session_collection = create_session_document_collection(session_id)
#         rag_agent.add_documents(documents, session_collection)
#         
#         # Determine file type and handle accordingly
#         file_type = "unknown"
#         if file.name.lower().endswith(('.xlsx', '.xls')):
#             file_type = "excel"
#         elif file.name.lower().endswith('.csv'):
#             file_type = "csv"
#         elif file.name.lower().endswith('.pdf'):
#             file_type = "pdf"
#         elif file.name.lower().endswith(('.doc', '.docx')):
#             file_type = "docx"
#         elif file.name.lower().endswith('.txt'):
#             file_type = "txt"
#         
#         # Extract financial data if Excel/CSV file
#         if file_type in ["excel", "csv"]:
#             financial_data = extract_financial_data_from_excel(file.path)
#             cl.user_session.set("portfolio_data", financial_data)
#             
#             # Process through orchestrator for portfolio analysis
#             result = orchestrator.handle_file_upload(financial_data, file_type)
#             
#             if result["agent_type"] == "PORTFOLIO":
#                 portfolio_result = result["response"]
#                 
#                 # Extract key information for display
#                 coverage_analysis = portfolio_result.get("coverage_analysis", {})
#                 additional_coverage = coverage_analysis.get("additional_coverage_needed", 0)
#                 portfolio_data = portfolio_result.get("portfolio_data", {})
#                 total_assets = portfolio_data.get("total_assets", 0)
#                 
#                 await cl.Message(
#                     content=f"✅ **Portfolio Analysis Complete!**\n\n**Portfolio Summary:**\n• Total Assets: ${total_assets:,.2f}\n• Additional Coverage Needed: ${additional_coverage:,.2f}\n\nI've analyzed your portfolio and can now provide specific life insurance integration recommendations. Ask me about how life insurance fits into this portfolio!",
#                     author="Assistant"
#                 ).send()
#             else:
#                 await cl.Message(
#                     content=f"✅ **File Processed Successfully!**\n\nI've analyzed {file.name} and added it to our knowledge base for this session.",
#                     author="Assistant"
#                 ).send()
#         else:
#             # Handle other file types
#             result = orchestrator.handle_file_upload({"file_path": file.path}, file_type)
#             
#             await cl.Message(
#                 content=f"✅ **File Processed Successfully!**\n\nI've added {file.name} to our knowledge base for this session. You can now ask questions about the content in this document.",
#                 author="Assistant"
#             ).send()
#         
#         # Update session state
#         uploaded_files = cl.user_session.get("uploaded_files", [])
#         uploaded_files.append({
#             "name": file.name,
#             "path": file.path,
#             "size": file.size,
#             "type": file_type
#         })
#         cl.user_session.set("uploaded_files", uploaded_files)
#         
#     except Exception as e:
#         await cl.Message(
#             content=f"❌ **Error Processing File**\n\nI encountered an error while processing {file.name}: {str(e)}\n\nPlease try uploading a different file or contact support if the issue persists.",
#             author="Assistant"
#         ).send()


@cl.on_chat_end
async def end():
    """
    Clean up session when chat ends.
    """
    session_id = cl.user_session.get("session_id")
    
    # Clear session documents
    if session_id:
        rag_agent.clear_session_documents(session_id)
    
    # Clean up uploaded files
    uploaded_files = cl.user_session.get("uploaded_files", [])
    for file_info in uploaded_files:
        try:
            if os.path.exists(file_info["path"]):
                os.remove(file_info["path"])
        except Exception as e:
            print(f"Warning: Could not remove file {file_info['path']}: {e}")


if __name__ == "__main__":
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your environment variables.")
        exit(1)
    
    # Start the Chainlit app
    cl.run() 