# Robo-Advisor Chatbot Configuration
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from root directory .env file (if it exists)
# This works for localhost development, but Render uses environment variables directly
env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists(env_file_path):
    load_dotenv(dotenv_path=env_file_path)
    print(f"🔧 Loaded .env file from: {env_file_path}")
else:
    print(f"🔧 No .env file found at: {env_file_path} - using environment variables directly")

class ChatbotConfig(BaseSettings):
    """Configuration for the Robo-Advisor Chatbot"""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o-mini"  # Use more cost-effective model
    openai_temperature: float = 0.1
    
    # Qdrant Configuration - Environment-aware
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_url: str = os.getenv("QDRANT_URL", "")  # Railway provides full URL
    qdrant_collection_name: str = "robo_advisor_rag"
    qdrant_sessions_collection: str = "robo_advisor_sessions"
    
    # LangSmith Configuration
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "robo-advisor-chatbot")
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    
    # Tavily Configuration
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    
    # Backend API Configuration
    backend_api_url: str = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    
    # Environment Configuration
    is_production: bool = False  # Will be set in __init__
    
    def __init__(self):
        super().__init__()
        # Debug: Log the actual backend URL being used
        print(f"🔧 Backend API URL configured as: {self.backend_api_url}")
        print(f"🔧 BACKEND_API_URL env var: {os.getenv('BACKEND_API_URL', 'NOT_SET')}")
        print(f"🔧 Environment: {'Render' if os.getenv('RENDER') else 'Localhost'}")
        print(f"🔧 All env vars starting with BACKEND: {[k for k in os.environ.keys() if k.startswith('BACKEND')]}")
        
        # Environment detection and Qdrant configuration
        # Detect production environment (Render, EC2, or other cloud)
        self.is_production = (
            os.getenv('RENDER') is not None or  # Render deployment
            os.getenv('AWS_EXECUTION_ENV') is not None or  # AWS Lambda/ECS
            os.getenv('EC2_INSTANCE_ID') is not None or  # EC2 instance
            os.path.exists('/.dockerenv')  # Docker container
        )
        
        # Fix RAG documents path for production vs localhost
        if self.is_production:
            # Production: chatbot directory is root, so RAG Documents is at ./RAG Documents
            self.rag_documents_path = os.path.join(os.getcwd(), "RAG Documents")
        else:
            # Localhost: RAG Documents is one level up from core directory
            self.rag_documents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "RAG Documents")
        
        self._configure_qdrant_for_environment()
    
    def _configure_qdrant_for_environment(self):
        """Configure Qdrant settings based on environment"""
        if self.is_production:
            # Production: Check if we're in Docker Compose (EC2) or Railway
            if self.qdrant_url:
                print(f"🔧 Production Qdrant URL: {self.qdrant_url}")
            elif os.path.exists('/.dockerenv'):
                # Docker Compose environment (EC2) - use Docker service name
                self.qdrant_host = "qdrant"
                self.qdrant_port = 6333
                print(f"🔧 Docker Compose Qdrant: {self.qdrant_host}:{self.qdrant_port}")
            else:
                # Railway or other cloud deployment
                if not self.qdrant_host or self.qdrant_host == "localhost":
                    self.qdrant_host = "qdrant-production-cf1d.up.railway.app"
                print(f"🔧 Cloud Qdrant: {self.qdrant_host}:{self.qdrant_port}")
        else:
            # Localhost: Use local Qdrant
            if self.qdrant_host == ":memory:":
                self.qdrant_host = "localhost"
            if self.qdrant_port == 0:
                self.qdrant_port = 6333
            print(f"🔧 Localhost Qdrant: {self.qdrant_host}:{self.qdrant_port}")
        
        # Log final configuration
        if self.qdrant_url:
            print(f"🔧 Final Qdrant config: URL={self.qdrant_url}")
        else:
            print(f"🔧 Final Qdrant config: {self.qdrant_host}:{self.qdrant_port}")
        
        # Calculate RAG documents path for logging
        rag_docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "RAG Documents")
        print(f"🔧 RAG Documents path: {rag_docs_path}")
        print(f"🔧 RAG Documents exists: {os.path.exists(rag_docs_path)}")
    
    # RAG Configuration - Updated for chatbot folder structure
    # In production (Render), the chatbot directory is the root, so RAG Documents is at ./RAG Documents
    # In localhost, it's at ../RAG Documents from the core directory
    rag_documents_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "RAG Documents")
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "text-embedding-3-small"  # Use smaller, cheaper model
    
    # Quality Thresholds
    min_rag_confidence: float = 0.7  # Lower threshold for better coverage
    min_search_confidence: float = 0.55  # Lowered from 0.6 to allow more external search results
    min_overall_confidence: float = 0.5
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    supported_file_types: list = [".pdf", ".csv", ".xlsx", ".xls", ".docx", ".doc", ".txt"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env file

# Global configuration instance
config = ChatbotConfig() 