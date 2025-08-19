import os
from typing import Optional
from pydantic_settings import BaseSettings

class ChatbotConfig(BaseSettings):
    """Configuration for the Robo-Advisor Chatbot"""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.1
    
    # Qdrant Configuration
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_collection_name: str = "robo_advisor_rag"
    
    # LangSmith Configuration
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "robo-advisor-chatbot")
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    
    # Tavily Configuration
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    
    # RAG Configuration
    rag_documents_path: str = "RAG Documents"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "text-embedding-3-small"
    
    # Quality Thresholds
    min_rag_confidence: float = 0.8
    min_search_confidence: float = 0.7
    min_overall_confidence: float = 0.6
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    supported_file_types: list = [".pdf", ".csv", ".xlsx", ".xls", ".docx", ".doc", ".txt"]
    
    class Config:
        env_file = ".env"

# Global configuration instance
config = ChatbotConfig() 