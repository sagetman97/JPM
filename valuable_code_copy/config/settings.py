"""
Configuration settings for the Financial Advisor Life Insurance Assistant.
Based on patterns from AIE7 course materials.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "20"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # External APIs
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    COHERE_API_KEY: Optional[str] = os.getenv("COHERE_API_KEY")
    
    # LangSmith Monitoring
    LANGSMITH_API_KEY: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "financial-advisor-assistant")
    
    # Qdrant Vector Database
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION_NAME: str = "financial_advisor_docs"
    
    # Application Settings
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # File Processing
    SUPPORTED_FILE_TYPES = [".pdf", ".txt", ".md", ".docx", ".xlsx", ".csv"]
    MAX_FILE_SIZE_MB: int = 50
    
    # RAG Settings
    TOP_K_RETRIEVAL: int = 3
    RERANK_TOP_K: int = 2
    
    # Calculator Settings
    DEFAULT_INCOME_MULTIPLE: float = 10.0
    MIN_COVERAGE_AMOUNT: int = 100000
    MAX_COVERAGE_AMOUNT: int = 10000000
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        return True

# Global settings instance
settings = Settings() 