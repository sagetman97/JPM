# Robo-Advisor Chatbot (Port 8001)

This directory contains the new Robo-Advisor chatbot system, designed to run independently from the existing portfolio tools.

## 🏗️ Architecture

### **Two-VM Structure:**
- **Port 8000**: Existing Portfolio Tools (CSV parsing, life insurance calculations)
- **Port 8001**: New Chatbot System (RAG, intent classification, tool integration)

### **Directory Structure:**
```
chatbot/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Chatbot dependencies (newer versions)
├── api/                   # API endpoints
├── core/                  # Core chatbot components
├── services/              # Service layer (RAG, search, etc.)
├── schemas/               # Data models
├── config/                # Configuration
└── tests/                 # Test files
```

## 🚀 Quick Start

### **1. Start Existing Portfolio Tools (Port 8000):**
```bash
./start_existing_tools.sh
```

### **2. Start Chatbot (Port 8001):**
```bash
./start_chatbot.sh
```

### **3. Access Services:**
- **Portfolio Tools**: http://localhost:8000
- **Chatbot API**: http://localhost:8001
- **Frontend**: http://localhost:3000

## 🔧 Dependencies

### **Chatbot Requirements (Port 8001):**
- `openai>=1.99.9` (newer version)
- `langchain`, `langgraph`, `ragas`
- `qdrant-client` for vector database
- `fastapi`, `uvicorn` for API

### **Existing Tools Requirements (Port 8000):**
- `openai==1.3.7` (older version for compatibility)
- `pandas`, `numpy` for data processing
- `fastapi`, `uvicorn` for API

## 🔗 Cross-Service Communication

### **Tool Integration:**
- Chatbot routes users to portfolio tools via deep links
- Portfolio tools send results back via webhooks
- Session continuity maintained across services

### **Webhook Endpoints:**
- **Port 8000**: `/api/webhook/portfolio-complete`
- **Port 8001**: `/api/webhook/tool-response`

## 📁 Key Files

- **`main.py`**: FastAPI app with chatbot endpoints
- **`core/orchestrator.py`**: Main chatbot orchestration
- **`core/intent_classifier.py`**: Semantic intent classification
- **`core/smart_router.py`**: Intelligent routing to tools
- **`services/rag_system.py`**: RAG and document processing
- **`services/file_processor.py`**: File upload and analysis

## 🧪 Testing

```bash
cd chatbot
python tests/test_chatbot.py
```

## 🚨 Important Notes

1. **Dependencies are separate** - each service has its own requirements
2. **Ports are different** - no conflicts between services
3. **Environment variables** are shared via root `.env` file
4. **RAG Documents** are shared between both services
5. **Cross-service communication** via HTTP webhooks

## 🔄 Development Workflow

1. **Existing Tools**: Work in `backend/` directory
2. **Chatbot**: Work in `chatbot/` directory
3. **Shared Resources**: Use root directory for shared files
4. **Testing**: Test each service independently
5. **Integration**: Test cross-service communication 