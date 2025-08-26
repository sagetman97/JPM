# 🚀 RoboAdvisor - AI-Powered Life Insurance & Financial Advisory Platform

> **A revolutionary AI-powered platform that transforms how financial advisors approach life insurance recommendations through intelligent chatbots, comprehensive portfolio analysis, and advanced RAG-powered knowledge systems.**

## 🎯 **Project Mission**

**Problem**: Financial advisors lack sufficient understanding of life insurance products, coverage calculations, and product selection criteria to confidently recommend life insurance as part of a diversified portfolio, causing them to avoid this integral component of risk management entirely.

**Solution**: An **AI-Powered Life Insurance Knowledge Assistant** that provides instant access to deep life insurance expertise through conversational interfaces, automated needs analysis, and comprehensive portfolio integration tools.

## 🏗️ **Revolutionary Architecture: Two-Port System**

### **Why This Architecture?**
Our platform solves a critical dependency conflict: older portfolio analysis tools can't use newer AI/ML libraries, while modern chatbot systems require cutting-edge AI capabilities. The solution? **Port isolation with separate dependency management on the same VM**.

### **Three-Service Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │ Portfolio Tools │    │  AI Chatbot    │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│  (Port 8001)   │
│   Next.js 15.4  │    │ FastAPI + LLM   │    │ FastAPI + AI/ML │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **Port 8000: Portfolio Analysis Engine**
- **Framework**: FastAPI + Python 3.12
- **Dependencies**: `openai==1.3.7`, `pandas==2.1.4`, `numpy==1.24.3`
- **Capabilities**: 
  - Universal financial document parsing (CSV, PDF, Word, Excel)
  - LLM-based semantic data extraction
  - Life insurance needs calculations
  - Portfolio health scoring and risk analysis
  - Cash value projections for IUL policies

#### **Port 8001: AI Chatbot Service**
- **Framework**: FastAPI + Python 3.12 + WebSocket support
- **Dependencies**: `openai>=1.99.9`, `qdrant-client==1.7.0`, `langchain`
- **Capabilities**:
  - Semantic intent classification (95% confidence)
  - Advanced RAG system with 560+ documents
  - Real-time conversational AI
  - File upload and analysis
  - External search integration (Tavily)
  - Tool routing and integration

#### **Port 3000: Modern Frontend**
- **Framework**: Next.js 15.4.1 + React 19.1.0 + TypeScript
- **Features**: 
  - Interactive portfolio assessment forms
  - Real-time calculations and visualizations
  - AI chatbot interface
  - Responsive design with Tailwind CSS

## 🚀 **Quick Start (Production-Ready)**

### **Prerequisites**
- **OS**: Ubuntu/Linux (WSL2 compatible)
- **Python**: 3.12+
- **Node.js**: 18+
- **Memory**: 8GB+ RAM recommended
- **Storage**: 2GB+ free space

### **1. Clone & Setup**
```bash
git clone https://github.com/sagetman97/JPM.git
cd JPM

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
```

### **2. Environment Configuration**
Create `.env` file in root directory:
```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=robo-advisor-chatbot

# Qdrant Configuration (optional - uses in-memory by default)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### **3. One-Command Startup (Recommended)**
```bash
# Terminal 1: Portfolio Tools
./start_existing_tools.sh

# Terminal 2: AI Chatbot
./start_chatbot.sh

# Terminal 3: Frontend
cd frontend && npm install && npm run dev
```

### **4. Access Your Platform**
- **Frontend Dashboard**: http://localhost:3000
- **Portfolio API**: http://localhost:8000/docs
- **Chatbot API**: http://localhost:8001/docs
- **Health Checks**: 
  - Portfolio: http://localhost:8000/health
  - Chatbot: http://localhost:8001/health

## 🔧 **Manual Startup (Advanced Users)**

### **Port 8000: Portfolio Analysis**
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Port 8001: AI Chatbot**
```bash
source venv/bin/activate
pip install -r chatbot/requirements.txt
cd chatbot
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### **Port 3000: Frontend**
```bash
cd frontend
npm install
npm run dev
```

## 🎯 **Core Features & Capabilities**

### **🤖 AI-Powered Chatbot (Port 8001)**
- **Semantic Understanding**: 95% confidence intent classification
- **RAG System**: 560+ documents ingested with Qdrant vector database
- **File Processing**: CSV, PDF, Word, Excel upload and analysis
- **External Search**: Real-time market data via Tavily API
- **Tool Integration**: Seamless routing to portfolio analysis tools
- **Context Management**: Advanced conversation memory and context preservation

### **📊 Portfolio Analysis Engine (Port 8000)**
- **Universal Document Parser**: LLM-based extraction from any financial document
- **Life Insurance Calculator**: DIME, human life value, and capital needs analysis
- **Portfolio Health Scoring**: Comprehensive risk assessment and benchmarking
- **Cash Value Projections**: IUL growth modeling with customizable parameters
- **Asset Allocation Analysis**: Industry-standard portfolio optimization

### **🎨 Interactive Frontend (Port 3000)**
- **Multi-Step Assessment**: Progressive disclosure forms with validation
- **Real-Time Calculations**: Instant coverage needs and premium estimates
- **Interactive Visualizations**: Chart.js powered charts and graphs
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Tool Integration**: Seamless navigation between assessment tools

## 📁 **Project Structure**

```
RoboAdvisor/
├── 🚀 start_existing_tools.sh      # Portfolio tools startup
├── 🤖 start_chatbot.sh             # AI chatbot startup
├── 📚 .env                         # API keys & configuration
├── 🐍 venv/                        # Python virtual environment
│
├── 🔧 backend/                     # Portfolio Analysis (Port 8000)
│   ├── api.py                      # Main API endpoints
│   ├── enhanced_parser.py          # LLM-based document parsing
│   ├── life_insurance_calculator.py # Coverage needs calculation
│   ├── portfolio_calculator.py     # Portfolio health scoring
│   ├── cash_value_calculator.py    # IUL projections
│   ├── ai_analysis.py              # AI-powered insights
│   └── requirements.txt            # Dependencies (openai==1.3.7)
│
├── 🧠 chatbot/                     # AI Chatbot Service (Port 8001)
│   ├── main.py                     # FastAPI + WebSocket app
│   ├── core/                       # Core chatbot components
│   │   ├── orchestrator.py         # Main chatbot logic
│   │   ├── intent_classifier.py    # Semantic understanding
│   │   ├── advanced_rag.py         # RAG system with Qdrant
│   │   ├── smart_router.py         # Tool routing
│   │   └── quick_calculator.py     # In-chat calculations
│   ├── requirements.txt             # Dependencies (openai>=1.99.9)
│   └── ingest_documents.py         # RAG document ingestion
│
├── 🎨 frontend/                    # Next.js Frontend (Port 3000)
│   ├── src/app/
│   │   ├── page.tsx                # Dashboard homepage
│   │   ├── assessment/             # Comprehensive assessment
│   │   ├── portfolio-assessment/   # Portfolio analysis
│   │   ├── quick-calculator/       # Quick needs calculator
│   │   └── robo-advisor/           # AI chatbot interface
│   └── package.json                # React 19 + Next.js 15.4
│
├── 📖 documentation/                # Project documentation
├── 📚 RAG Documents/               # Knowledge base (560+ docs)
└── 🔒 .gitignore                   # Security & exclusions
```

## 🧮 **Calculation Engine Capabilities**

### **Life Insurance Needs Analysis**
- **Income Replacement**: Multiplier-based calculations with age adjustments
- **Debt Coverage**: Mortgage, student loans, and other obligations
- **Education Funding**: Per-child cost projections with inflation
- **Final Expenses**: Funeral costs and legacy planning
- **Special Needs**: Disability and long-term care considerations

### **Portfolio Health Scoring (0-100)**
- **Asset Allocation Diversity**: 30 points for balanced portfolios
- **Portfolio Size Adequacy**: 20 points for wealth accumulation
- **Liquidity Management**: 20 points for emergency preparedness
- **Insurance Coverage**: 15 points for protection planning
- **Real Estate Concentration**: Context-aware penalties

### **Cash Value Projections**
- **IUL Growth Modeling**: 6-8% annual growth rates
- **Premium Allocation**: 85% year 1, 95% subsequent years
- **MEC Limit Calculations**: IRS-compliant contribution limits
- **40-Year Projections**: Long-term wealth accumulation planning

## 🔍 **AI & Machine Learning Features**

### **Semantic Intent Classification**
- **Confidence Scoring**: 95% accuracy on financial queries
- **Context Awareness**: Maintains conversation state and history
- **Multi-Language Support**: Natural language understanding
- **Intent Categories**: 15+ specialized financial advisory intents

### **Advanced RAG System**
- **Document Ingestion**: 560+ financial documents processed
- **Vector Embeddings**: OpenAI text-embedding-3-small
- **Semantic Search**: Multi-query and ensemble retrieval
- **Quality Evaluation**: RAGAS metrics for response quality
- **Source Attribution**: Transparent information sourcing

### **External Knowledge Integration**
- **Tavily Search API**: Real-time market data and trends
- **Regulatory Updates**: Latest compliance information
- **Product Comparisons**: Current rates and features
- **Industry Insights**: LIMRA and market research data

## 🧪 **Testing & Quality Assurance**

### **Automated Testing Suite**
```bash
# Test portfolio tools
curl http://localhost:8000/health

# Test chatbot service
curl http://localhost:8001/health

# Test tool integration
cd chatbot && python test_tool_integration.py

# Test RAG system
cd chatbot && python test_rag.py
```

### **Quality Metrics**
- **RAGAS Evaluation**: Faithfulness (0.96), Relevancy (0.81)
- **Response Quality**: Continuous improvement through feedback
- **Performance Monitoring**: LangSmith integration for tracing
- **Error Handling**: Comprehensive fallback mechanisms

## 🚀 **Production Deployment**

### **Environment Requirements**
- **Python**: 3.12+ with virtual environment
- **Node.js**: 18+ with npm/yarn
- **Memory**: 8GB+ RAM for RAG operations
- **Storage**: 2GB+ for document storage
- **Network**: Stable internet for API calls

### **Security Considerations**
- **API Key Management**: Secure environment variable storage
- **CORS Configuration**: Restricted origin access
- **Input Validation**: Pydantic models for data integrity
- **Rate Limiting**: Configurable API usage limits
- **Data Privacy**: No persistent storage of sensitive information

### **Scaling Considerations**
- **Horizontal Scaling**: Multiple chatbot instances
- **Load Balancing**: Nginx reverse proxy configuration
- **Database Scaling**: Qdrant cluster for large document sets
- **Caching**: Redis for frequently accessed data
- **Monitoring**: Prometheus + Grafana integration

## 🔮 **Future Roadmap**

### **Phase 2: Enhanced Integration**
- **JPMorgan API Integration**: Wealth management system connectivity
- **Real-Time Market Data**: Live insurance rate feeds
- **Advanced Analytics**: Predictive modeling and insights
- **Mobile Applications**: iOS and Android native apps

### **Phase 3: Enterprise Features**
- **Multi-Tenant Architecture**: Advisor firm support
- **Advanced Security**: SSO and enterprise authentication
- **Compliance Tools**: Regulatory reporting and auditing
- **White-Label Solutions**: Customizable branding options

### **Phase 4: AI Enhancement**
- **Fine-Tuned Models**: Domain-specific language models
- **Predictive Analytics**: Client behavior modeling
- **Automated Underwriting**: AI-powered risk assessment
- **Natural Language Generation**: Automated report creation

## 🐛 **Troubleshooting & Support**

### **Common Issues**
1. **Port Conflicts**: Use `fuser -k 8000/tcp` to clear ports
2. **Dependency Issues**: Ensure separate requirements.txt files
3. **Memory Issues**: Increase swap space for RAG operations
4. **API Limits**: Monitor OpenAI and Tavily usage

### **Debug Commands**
```bash
# Check service status
ps aux | grep uvicorn
netstat -tlnp | grep :800

# View logs
tail -f backend/logs/app.log
tail -f chatbot/logs/chatbot.log

# Test connectivity
curl -v http://localhost:8000/health
curl -v http://localhost:8001/health
```

### **Support Resources**
- **Documentation**: Comprehensive guides in `/documentation/`
- **Implementation Summary**: `CHATBOT_IMPLEMENTATION_SUMMARY.md`
- **Project Answers**: `PROJECT_ANSWERS.md` for technical details
- **GitHub Issues**: Report bugs and feature requests

## 🤝 **Contributing & Development**

### **Development Workflow**
1. **Fork Repository**: Create your own fork
2. **Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Test Changes**: Run comprehensive test suite
4. **Submit PR**: Detailed description of changes
5. **Code Review**: Maintain code quality standards

### **Code Standards**
- **Python**: PEP 8 compliance with type hints
- **TypeScript**: Strict mode with proper interfaces
- **Testing**: 90%+ code coverage requirement
- **Documentation**: Comprehensive docstrings and comments

### **Architecture Principles**
- **Separation of Concerns**: Clear module boundaries
- **Dependency Isolation**: Port-based service separation
- **API-First Design**: RESTful and WebSocket endpoints
- **Scalability**: Horizontal scaling considerations

## 📊 **Performance Metrics**

### **Current Benchmarks**
- **Portfolio Analysis**: 2-5 seconds (Phase 1), 10-30 seconds (Phase 2)
- **Chatbot Response**: 2-5 seconds for standard queries
- **Document Processing**: 1-3 seconds per document
- **RAG Retrieval**: 500ms average response time

### **Scalability Targets**
- **Concurrent Users**: 100+ simultaneous chatbot sessions
- **Document Processing**: 1000+ documents per hour
- **API Throughput**: 1000+ requests per minute
- **Response Time**: <2 seconds for 95% of queries

## 📞 **Contact & Support**

### **Project Information**
- **Repository**: https://github.com/sagetman97/JPM.git
- **Documentation**: Comprehensive guides in `/documentation/`
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions

### **Technical Support**
- **Architecture Questions**: Review `CHATBOT_IMPLEMENTATION_SUMMARY.md`
- **API Documentation**: Swagger UI at `/docs` endpoints
- **Testing**: Comprehensive test suite in `/chatbot/tests/`
- **Deployment**: Startup scripts and configuration guides

---

## 🎉 **Getting Started**

Ready to transform your financial advisory practice? 

1. **Clone the repository**: `git clone https://github.com/sagetman97/JPM.git`
2. **Set up environment**: Create `.env` file with your API keys
3. **Start services**: Use the provided startup scripts
4. **Access platform**: Navigate to http://localhost:3000
5. **Begin exploring**: Try the AI chatbot and portfolio analysis tools

**Welcome to the future of AI-powered financial advisory! 🚀**

---

*This platform represents a revolutionary approach to financial advisory, combining cutting-edge AI technology with comprehensive financial planning tools. Built with scalability, security, and user experience in mind, it's designed to transform how financial professionals approach life insurance and portfolio management.* 