# 🚀 Valuable Code Copy - Financial Advisor Assistant

This folder contains the **most valuable and actively used code** extracted from the original Financial Advisor Assistant repository. All experimental, evaluation-only, and unused files have been excluded.

## 📁 What Was Copied (And Why)

### 🎯 **Core Application Files**
- **`app.py`** - Main Chainlit application with multi-agent orchestration
- **`load_data.py`** - Document loading and vector store initialization  
- **`setup.py`** - System setup and initialization

### 🤖 **Multi-Agent System (The Core Value)**
- **`agents/orchestrator.py`** - Coordinates all specialized agents
- **`agents/rag_agent.py`** - Enhanced RAG agent with advanced retrieval
- **`agents/query_router.py`** - Intelligent query routing system
- **`agents/calculator_agent.py`** - Life insurance needs calculation engine
- **`agents/portfolio_agent.py`** - Portfolio analysis and insurance integration
- **`agents/research_agent.py`** - External research and market data integration

### 🔍 **Advanced Retrieval System (Innovative)**
- **`retrieval/hybrid_search.py`** - BM25 + semantic search hybrid
- **`retrieval/ensemble.py`** - Ensemble retrieval methods
- **`retrieval/multi_query.py`** - Multi-query retrieval for complex questions
- **`retrieval/contextual_compression.py`** - Reranking and compression
- **`retrieval/semantic_chunking.py`** - Intelligent document chunking
- **`retrieval/parent_document.py`** - Parent-document retrieval strategy

### 🛠️ **Utility Functions (Practical)**
- **`utils/confidence.py`** - Confidence scoring for response quality
- **`utils/file_processing.py`** - File upload and processing utilities
- **`utils/chunking.py`** - Document chunking strategies
- **`utils/rate_limiter.py`** - API rate limiting utilities

### ⚙️ **Configuration (Essential)**
- **`config/settings.py`** - Configuration management with environment variables
- **`pyproject.toml`** - Project dependencies and build configuration
- **`env_example.txt`** - Environment variable template

## 🚫 **What Was NOT Copied (And Why)**

The following files were **excluded** because they are:
- **Experimental/Evaluation-only**: Not integrated into the main application
- **Testing scripts**: Development tools, not production code
- **Alternative implementations**: Unused code paths
- **Large binary files**: Qdrant executables, PDFs, etc.

**Excluded files:**
- All `evaluate_*.py` scripts (standalone evaluation)
- `ragas_evaluation_step_by_step.py` (standalone evaluation)
- `evaluate_system.py` (standalone evaluation)
- `test_*.py` scripts (testing only)
- `app_langgraph.py` (alternative implementation)
- `qdrant*` binaries and archives
- PDF documents and large data files
- Virtual environment folders

## 🏗️ **Key Architectural Patterns to Adapt**

### 1. **Multi-Agent Orchestration**
```python
# The orchestrator coordinates specialized agents
orchestrator = MultiAgentOrchestrator(
    llm=ChatOpenAI(...),
    rag_agent=rag_agent,
    tavily_api_key=settings.TAVILY_API_KEY
)
```

### 2. **Confidence-Based Routing**
```python
# Uses confidence scores to determine when to use external search
confidence_score = assess_confidence_score(response, query, retrieved_docs)
if confidence_score < settings.CONFIDENCE_THRESHOLD:
    # Use external search for additional context
```

### 3. **Advanced Retrieval Pipeline**
```python
# Multiple retrieval methods with ensemble approaches
retrievers = {
    "hybrid": HybridRetriever(...),
    "ensemble": EnsembleRetriever(...),
    "multi_query": EnhancedMultiQueryRetriever(...)
}
```

### 4. **Session Management**
```python
# Context-aware conversations with file uploads
session_context = {
    "session_id": session_id,
    "uploaded_files": [...],
    "portfolio_data": {...},
    "client_info": {...}
}
```

## 🚀 **How to Use This Code for Your New Bot**

### 1. **Adapt the Agent Architecture**
- Replace life insurance specific logic with your domain
- Keep the multi-agent orchestration pattern
- Adapt the confidence scoring for your use case

### 2. **Customize the Retrieval System**
- The advanced retrieval techniques are domain-agnostic
- Adapt the chunking strategies for your documents
- Modify the ensemble retrieval for your specific needs

### 3. **Update Configuration**
- Modify `config/settings.py` for your requirements
- Update `pyproject.toml` with your dependencies
- Adapt environment variables in `env_example.txt`

### 4. **Integrate Your Knowledge Base**
- Replace the life insurance documents with your domain data
- Update the RAG agent prompts for your use case
- Modify file processing for your document types

## 📋 **Dependencies to Install**

The core dependencies you'll need:
```bash
pip install langchain langchain-openai langchain-qdrant
pip install chainlit qdrant-client tavily-python
pip install pandas pymupdf python-docx openpyxl
pip install ragas scikit-learn nltk
```

## 🎯 **Most Valuable Patterns to Copy**

1. **Agent Coordination**: How agents communicate and share context
2. **Confidence Assessment**: When to use external sources vs. RAG
3. **Retrieval Ensemble**: Combining multiple retrieval methods
4. **Session State Management**: Maintaining conversation context
5. **File Processing Pipeline**: Handling multiple file types
6. **Error Handling**: Graceful degradation and user feedback

## 💡 **Quick Start for New Bot**

1. **Copy this entire folder** to your new project
2. **Update the domain-specific logic** in agent prompts
3. **Replace the knowledge base** with your documents
4. **Adapt the confidence scoring** for your use case
5. **Test the multi-agent orchestration** with your queries

This code provides a **production-ready foundation** for any multi-agent RAG system with advanced retrieval capabilities! 