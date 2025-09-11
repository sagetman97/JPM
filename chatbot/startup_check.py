#!/usr/bin/env python3
"""
Comprehensive startup check for the RoboAdvisor Chatbot.
This script verifies all components are working before starting the service.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the chatbot directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import config
from core.advanced_rag import EnhancedRAGSystem
from core.session_persistence import SessionPersistenceManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StartupChecker:
    """Comprehensive startup checker for the chatbot service"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
    def log_success(self, message: str):
        """Log a successful check"""
        logger.info(f"✅ {message}")
        self.success_count += 1
    
    def log_warning(self, message: str):
        """Log a warning"""
        logger.warning(f"⚠️ {message}")
        self.warnings.append(message)
    
    def log_error(self, message: str):
        """Log an error"""
        logger.error(f"❌ {message}")
        self.errors.append(message)
    
    async def check_environment(self):
        """Check environment configuration"""
        logger.info("🔧 Checking environment configuration...")
        
        # Check if we're in production or localhost
        if config.is_production:
            self.log_success("Running in production mode")
        else:
            self.log_success("Running in localhost mode")
        
        # Check Qdrant configuration
        logger.info(f"Qdrant Host: {config.qdrant_host}")
        logger.info(f"Qdrant Port: {config.qdrant_port}")
        if config.qdrant_url:
            logger.info(f"Qdrant URL: {config.qdrant_url}")
        else:
            logger.info("Qdrant URL: Not set (using host/port)")
        
        # Check RAG documents path
        if os.path.exists(config.rag_documents_path):
            doc_count = len(list(Path(config.rag_documents_path).iterdir()))
            self.log_success(f"RAG Documents folder found with {doc_count} items")
        else:
            self.log_error(f"RAG Documents folder not found at: {config.rag_documents_path}")
    
    async def check_qdrant_connection(self):
        """Check Qdrant connection"""
        logger.info("🔗 Checking Qdrant connection...")
        
        try:
            rag_system = EnhancedRAGSystem()
            
            if rag_system.qdrant_available:
                self.log_success("Qdrant connection established")
                
                # Check if collection exists
                try:
                    collection_info = rag_system.collection_info
                    if collection_info:
                        self.log_success(f"RAG collection exists with {collection_info.vectors_count} documents")
                    else:
                        self.log_warning("RAG collection exists but info unavailable")
                except Exception as e:
                    self.log_warning(f"Could not get collection info: {e}")
                
                # Check if documents are loaded
                if rag_system.has_documents():
                    self.log_success("RAG database has documents loaded")
                else:
                    self.log_warning("RAG database is empty - documents need to be ingested")
                    
            else:
                self.log_error("Qdrant connection failed")
                
        except Exception as e:
            self.log_error(f"Qdrant connection failed: {e}")
    
    async def check_session_persistence(self):
        """Check session persistence system"""
        logger.info("💾 Checking session persistence...")
        
        try:
            # Try to get Qdrant client from RAG system
            rag_system = EnhancedRAGSystem()
            session_manager = SessionPersistenceManager(rag_system.qdrant_client)
            
            if session_manager.use_qdrant:
                self.log_success("Session persistence using Qdrant")
            else:
                self.log_warning("Session persistence using in-memory storage")
            
            # Test session stats
            stats = session_manager.get_session_stats()
            logger.info(f"Session storage stats: {stats}")
            
        except Exception as e:
            self.log_error(f"Session persistence check failed: {e}")
    
    async def check_document_ingestion(self):
        """Check if documents need to be ingested"""
        logger.info("📚 Checking document ingestion status...")
        
        try:
            rag_system = EnhancedRAGSystem()
            
            if not rag_system.has_documents():
                if os.path.exists(config.rag_documents_path):
                    logger.info("📥 RAG database is empty - starting document ingestion...")
                    
                    success = await rag_system.ingest_documents()
                    if success:
                        self.log_success("Document ingestion completed successfully")
                    else:
                        self.log_error("Document ingestion failed")
                else:
                    self.log_error("Cannot ingest documents - RAG Documents folder not found")
            else:
                self.log_success("RAG database already has documents")
                
        except Exception as e:
            self.log_error(f"Document ingestion check failed: {e}")
    
    async def check_environment_variables(self):
        """Check required environment variables"""
        logger.info("🔑 Checking environment variables...")
        
        required_vars = {
            'OPENAI_API_KEY': 'OpenAI API key for LLM access'
        }
        
        optional_vars = {
            'QDRANT_URL': 'Qdrant connection URL (Railway provides this)',
            'QDRANT_HOST': 'Qdrant host (fallback if URL not provided)',
            'QDRANT_PORT': 'Qdrant port (fallback if URL not provided)',
            'TAVILY_API_KEY': 'Tavily API key for external search',
            'LANGSMITH_API_KEY': 'LangSmith API key for monitoring',
            'BACKEND_API_URL': 'Backend API URL for portfolio tools'
        }
        
        # Check required variables
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                if var in ['OPENAI_API_KEY']:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "SET"
                else:
                    display_value = value
                self.log_success(f"{var}: {display_value}")
            else:
                self.log_error(f"{var}: NOT SET - {description}")
        
        # Check optional variables
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                if var in ['OPENAI_API_KEY', 'TAVILY_API_KEY', 'LANGSMITH_API_KEY']:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "SET"
                else:
                    display_value = value
                self.log_success(f"{var}: {display_value}")
            else:
                self.log_warning(f"{var}: NOT SET - {description} (optional)")
    
    async def run_all_checks(self):
        """Run all startup checks"""
        logger.info("🚀 Starting RoboAdvisor Chatbot startup checks...")
        logger.info("=" * 60)
        
        await self.check_environment()
        await self.check_environment_variables()
        await self.check_qdrant_connection()
        await self.check_session_persistence()
        await self.check_document_ingestion()
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 STARTUP CHECK SUMMARY")
        logger.info(f"✅ Successful checks: {self.success_count}")
        logger.info(f"⚠️ Warnings: {len(self.warnings)}")
        logger.info(f"❌ Errors: {len(self.errors)}")
        
        if self.warnings:
            logger.info("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                logger.info(f"   - {warning}")
        
        if self.errors:
            logger.info("\n❌ ERRORS:")
            for error in self.errors:
                logger.info(f"   - {error}")
            
            logger.error("\n🚨 STARTUP FAILED - Fix errors before starting the service")
            return False
        else:
            logger.info("\n🎉 STARTUP SUCCESSFUL - Service is ready to start")
            return True

async def main():
    """Main startup check function"""
    checker = StartupChecker()
    success = await checker.run_all_checks()
    
    if success:
        logger.info("✅ All checks passed - service can start")
        sys.exit(0)
    else:
        logger.error("❌ Some checks failed - service should not start")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
