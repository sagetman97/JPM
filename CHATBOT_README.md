# 🤖 Robo-Advisor Chatbot System

A sophisticated, human-feeling conversational AI specialized in life insurance and financial planning, built with semantic understanding throughout the entire architecture.

## 🎯 **Features**

- **Semantic Understanding**: Deep comprehension of user intent, not just keyword matching
- **Human-Feeling Conversation**: Natural flow with context awareness and goal orientation
- **Smart Routing**: Intelligent selection of information sources and tools
- **Quality Assurance**: Multi-layer evaluation with agent-based improvement
- **Compliance-First**: Built-in legal guardrails and regulatory compliance
- **Seamless Tool Integration**: Works with existing platform tools and workflows

## 🏗️ **Architecture**

```
User Query → Intent Classification → Smart Router → Response Generation → Quality Check → Compliance Review → Final Response
```

### **Core Components**

1. **Semantic Intent Classifier**: LLM-only intent classification with context awareness
2. **Smart Router**: Confidence-based routing to RAG, external search, or tools
3. **Semantic RAG System**: Vector database with OpenAI embeddings and Qdrant
4. **External Search**: Tavily API integration with quality evaluation
5. **Tool Integrator**: Seamless integration with existing platform tools
6. **Quality Evaluator**: Multi-layer response quality assessment
7. **Compliance Agent**: Legal guardrails and regulatory compliance

## 🚀 **Quick Start**

### **1. Prerequisites**

- Python 3.8+
- Docker (for Qdrant)
- OpenAI API key
- Tavily API key (optional)
- LangSmith API key (optional)

### **2. Environment Setup**

Create a `.env` file in the root directory:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# LangSmith Configuration (optional)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=robo-advisor-chatbot

# Tavily Configuration (optional)
TAVILY_API_KEY=your_tavily_api_key_here
```

### **3. Automated Setup**

Run the startup script:

```bash
./start_chatbot.sh
```

This will:
- Check and start Qdrant if needed
- Create virtual environment
- Install dependencies
- Test all components

### **4. Manual Setup**

If you prefer manual setup:

```bash
# Start Qdrant
docker run -d --name qdrant-chatbot -p 6333:6333 qdrant/qdrant:latest

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements_chatbot.txt

# Test components
cd backend
python test_chatbot.py
```

### **5. Start the System**

```bash
# Terminal 1: Start Backend
cd backend
python -m uvicorn main:app --reload

# Terminal 2: Start Frontend
cd frontend
npm run dev
```

### **6. Access the Chatbot**

- **Frontend**: http://localhost:3000/robo-advisor
- **Backend API**: http://localhost:8000/chatbot
- **Health Check**: http://localhost:8000/chatbot/health

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | Required |
| `QDRANT_HOST` | Qdrant vector database host | `localhost` |
| `QDRANT_PORT` | Qdrant vector database port | `6333` |
| `LANGSMITH_API_KEY` | LangSmith monitoring API key | Optional |
| `LANGSMITH_PROJECT` | LangSmith project name | `robo-advisor-chatbot` |
| `TAVILY_API_KEY` | Tavily search API key | Optional |

### **RAG Configuration**

The system automatically loads documents from the `RAG Documents/` folder:

- **Text files** (`.txt`, `.md`): Direct processing
- **PDF files** (`.pdf`): Text extraction and processing
- **Office files** (`.docx`, `.xlsx`): Text extraction and processing

## 📚 **API Endpoints**

### **WebSocket Endpoints**

- `ws://localhost:8000/chatbot/ws/chat/{session_id}` - Real-time chat

### **HTTP Endpoints**

- `POST /chatbot/api/chat/process` - Process chat message
- `GET /chatbot/api/chat/session/{session_id}` - Get session info
- `DELETE /chatbot/api/chat/session/{session_id}` - Clean up session
- `POST /chatbot/api/chat/cleanup` - Clean up inactive sessions
- `GET /chatbot/health` - Health check

## 🧮 **Calculator Integration**

### **Three Calculator Types**

1. **Quick Calculator** (In-Chat)
   - 5 basic questions for immediate estimate
   - Conversational data collection
   - Real-time results

2. **Detailed Assessment** (External Tool)
   - Comprehensive 50+ question assessment
   - Opens in new tab/popup
   - Report returned to chatbot

3. **Portfolio Analysis** (External Tool)
   - Portfolio-focused insurance analysis
   - Integrates with existing portfolio tools
   - Comprehensive report integration

### **Tool Routing**

The chatbot intelligently routes users to the appropriate calculator based on:

- **Semantic understanding** of their request
- **Knowledge level** assessment
- **Context** from conversation history
- **Goals** expressed by the user

## 🔍 **RAG & Search Strategy**

### **Semantic RAG System**

- **Embeddings**: OpenAI text-embedding-3-small
- **Vector Database**: Qdrant with cosine similarity
- **Chunking**: 1000 tokens with 200 token overlap
- **Context Awareness**: Conversation history integration

### **External Search Integration**

- **Search Engine**: Tavily API
- **Quality Evaluation**: LLM-based assessment
- **Retry Logic**: Multiple search strategies
- **Fallback Handling**: Graceful degradation

### **Quality Gates**

- **RAG Confidence**: > 0.8 for direct response
- **Search Confidence**: > 0.7 for external sources
- **Overall Confidence**: > 0.6 for response surfacing

## 📊 **Quality Evaluation**

### **Evaluation Metrics**

1. **RAGAS Metrics**
   - Faithfulness
   - Answer Relevancy
   - Context Precision
   - Context Recall

2. **Semantic Quality**
   - Intent Alignment
   - Context Continuity
   - Knowledge Appropriateness
   - Goal Relevance
   - Semantic Completeness

3. **User Satisfaction**
   - Predicted helpfulness
   - Response relevance

### **Quality Improvement**

- **Agent-Based Enhancement**: Automatic improvement of low-quality responses
- **Multi-Strategy Retry**: Different approaches for failed responses
- **Continuous Learning**: Feedback integration for improvement

## 🔒 **Compliance & Safety**

### **Compliance Features**

- **Legal Disclaimers**: Automatic insertion when needed
- **Risk Assessment**: Content risk evaluation
- **Regulatory Compliance**: Financial regulation adherence
- **Response Rewriting**: Automatic compliance adjustments

### **Safety Guardrails**

- **Content Filtering**: Sensitive topic detection
- **Advice Limitations**: Educational content only
- **Professional Consultation**: Encouragement for expert advice
- **Risk Warnings**: Appropriate risk disclosures

## 🚀 **Development & Testing**

### **Running Tests**

```bash
cd backend
python test_chatbot.py
```

### **Component Testing**

```bash
# Test individual components
python -c "from chatbot.intent_classifier import SemanticIntentClassifier; print('✅ Intent Classifier OK')"
python -c "from chatbot.rag_system import SemanticRAGSystem; print('✅ RAG System OK')"
python -c "from chatbot.orchestrator import ChatbotOrchestrator; print('✅ Orchestrator OK')"
```

### **API Testing**

```bash
# Test health endpoint
curl http://localhost:8000/chatbot/health

# Test chat processing
curl -X POST http://localhost:8000/chatbot/api/chat/process \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-123"}'
```

## 📁 **Project Structure**

```
backend/
├── chatbot/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── schemas.py             # Pydantic data models
│   ├── intent_classifier.py   # Semantic intent classification
│   ├── smart_router.py        # Intelligent routing system
│   ├── rag_system.py          # RAG with vector database
│   ├── external_search.py     # External search integration
│   └── orchestrator.py        # Main orchestration logic
├── chatbot_api.py             # FastAPI endpoints
├── requirements_chatbot.txt   # Chatbot dependencies
├── test_chatbot.py           # Component testing
└── main.py                   # Main FastAPI app

RAG Documents/                 # Knowledge base documents
start_chatbot.sh              # Automated startup script
CHATBOT_README.md             # This file
```

## 🔮 **Future Enhancements**

### **Phase 2: Advanced Features**

- **LangChain Integration**: Enhanced LLM orchestration
- **LangGraph Workflows**: Complex multi-agent workflows
- **Advanced Retrieval**: Hybrid search strategies
- **Fine-tuned Models**: Domain-specific model training

### **Phase 3: Production Features**

- **Monitoring Dashboard**: Real-time system monitoring
- **Performance Analytics**: Response time and quality metrics
- **User Feedback Integration**: Continuous improvement loop
- **Multi-language Support**: Internationalization

### **Phase 4: Enterprise Features**

- **Multi-tenant Support**: Organization isolation
- **Advanced Security**: Role-based access control
- **Audit Logging**: Comprehensive activity tracking
- **API Rate Limiting**: Usage management

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Qdrant Connection Failed**
   ```bash
   # Check if Qdrant is running
   curl http://localhost:6333/collections
   
   # Start Qdrant if needed
   docker run -d --name qdrant-chatbot -p 6333:6333 qdrant/qdrant:latest
   ```

2. **OpenAI API Error**
   ```bash
   # Check API key in .env
   cat .env | grep OPENAI_API_KEY
   
   # Verify API key is valid
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```

3. **Import Errors**
   ```bash
   # Activate virtual environment
   source venv/bin/activate
   
   # Reinstall dependencies
   pip install -r backend/requirements_chatbot.txt
   ```

4. **Port Conflicts**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Kill conflicting processes
   pkill -f "uvicorn"
   ```

### **Logs & Debugging**

Enable debug logging by setting environment variable:

```bash
export LOG_LEVEL=DEBUG
```

Check logs in the terminal where you started the backend.

## 📞 **Support**

For issues and questions:

1. **Check the logs** for error messages
2. **Run the test script** to verify components
3. **Check configuration** in your `.env` file
4. **Verify services** are running (Qdrant, etc.)

## 📄 **License**

This project is part of the Robo-Advisor platform. Please refer to the main project license for usage terms.

---

**🎉 Congratulations!** You now have a sophisticated, human-feeling chatbot system that can understand user intent, provide intelligent responses, and integrate seamlessly with your existing financial tools. 