# Robo-Advisor Chatbot Configuration
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from root directory .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

class ChatbotConfig(BaseSettings):
    """Configuration for the Robo-Advisor Chatbot"""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o-mini"  # Use more cost-effective model
    openai_temperature: float = 0.1
    
    # Qdrant Configuration - Use in-memory by default
    qdrant_host: str = os.getenv("QDRANT_HOST", ":memory:")  # In-memory by default
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "0"))  # Port 0 for in-memory
    qdrant_collection_name: str = "robo_advisor_rag"
    
    # LangSmith Configuration
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "robo-advisor-chatbot")
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    
    # Tavily Configuration
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    
    # RAG Configuration
    rag_documents_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "RAG Documents")
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

# Global configuration instance
config = ChatbotConfig() 