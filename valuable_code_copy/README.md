# Financial Advisor Life Insurance Assistant

A multi-agent AI system designed to help financial advisors confidently recommend life insurance products to their clients. The system combines RAG knowledge base, external search, file analysis, and specialized calculators.

## 🎯 Features

### Multi-Agent System Architecture
- **Query Router Agent**: Intelligently routes queries to appropriate specialists
- **RAG Agent**: Access comprehensive life insurance knowledge base
- **Research Agent**: Combines RAG knowledge with external search for current information
- **Calculator Agent**: Interactive life insurance needs analysis with multiple methodologies
- **Portfolio Agent**: Analyzes uploaded financial data for insurance integration
- **Orchestrator**: Coordinates all agents and synthesizes comprehensive responses

### Core Capabilities
- **Intelligent Query Routing**: Automatically determines the best agent for each query type
- **Confidence-Based Escalation**: Uses external search when RAG confidence is low
- **Multi-Modal File Processing**: Upload portfolios (Excel, CSV, PDF) for analysis
- **Comprehensive Analysis**: Combines multiple perspectives for holistic recommendations
- **Real-time Market Data**: Access current rates and market conditions
- **Professional UI**: Clean, intuitive Chainlit interface for financial advisors

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API Key
- Tavily API Key (optional, for external search)
- Cohere API Key (optional, for reranking)

### Installation

1. **Clone and setup environment**:
```bash
cd financial_advisor_assistant
uv sync
```

2. **Set environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run the application**:
```bash
chainlit run app.py
```

## 📁 Project Structure

```
financial_advisor_assistant/
├── app.py                          # Main Chainlit application
├── agents/                         # Multi-agent system
│   ├── __init__.py
│   ├── orchestrator.py            # Multi-agent orchestrator
│   ├── query_router.py            # Query routing and agent selection
│   ├── rag_agent.py               # RAG knowledge base agent
│   ├── research_agent.py          # External search and research agent
│   ├── calculator_agent.py        # Life insurance calculator
│   └── portfolio_agent.py         # Portfolio analysis agent
├── data/                          # Life insurance documents
│   └── RAG Documents/             # Source documents
├── utils/                         # Utility functions
│   ├── __init__.py
│   ├── file_processing.py         # File upload processing
│   ├── confidence.py              # Confidence scoring
│   └── chunking.py                # Document chunking strategies
├── config/                        # Configuration files
│   ├── __init__.py
│   └── settings.py                # Application settings
├── test_multi_agent.py            # Test script for multi-agent system
├── load_data.py                   # Load initial RAG documents
└── setup.py                       # Project setup script
```

## 🔧 Configuration

The application uses environment variables for configuration:

```bash
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
COHERE_API_KEY=your_cohere_key
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=financial-advisor-assistant
```

## 🧪 Testing

### Test the Multi-Agent System

Run the test script to verify all agents are working correctly:

```bash
python test_multi_agent.py
```

This will:
- Test query routing to appropriate agents
- Verify confidence assessment functionality
- Demonstrate agent capabilities
- Show conversation flow and synthesis

### Manual Testing

You can also test the system interactively:

1. **Start the application**:
```bash
chainlit run app.py
```

2. **Test different query types**:
   - Knowledge questions: "What is whole life insurance?"
   - Calculator requests: "How much life insurance do I need?"
   - Portfolio analysis: "Upload a portfolio and ask about integration"
   - Research queries: "What are current term life rates?"

3. **Upload files** for portfolio analysis (Excel, CSV, PDF)

## 📊 Evaluation

Run the evaluation framework:

```bash
python evaluation/evaluation.py
```

This will:
- Generate synthetic test data
- Evaluate RAG performance with RAGAS
- Compare advanced retrieval techniques
- Provide performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details. 