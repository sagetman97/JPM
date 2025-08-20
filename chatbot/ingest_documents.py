#!/usr/bin/env python3
"""
RAG Document Ingestion Script
Ingests documents from the RAG Documents folder into Qdrant for the chatbot.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the chatbot directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from core.advanced_rag import EnhancedRAGSystem
from core.config import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main ingestion function"""
    
    try:
        logger.info("🚀 Starting RAG document ingestion...")
        
        # Initialize RAG system
        rag_system = EnhancedRAGSystem(external_search_system=None)  # No external search needed for ingestion
        
        # Check if documents path exists
        documents_path = Path(config.rag_documents_path)
        if not documents_path.exists():
            logger.error(f"❌ RAG documents path does not exist: {documents_path}")
            return False
        
        logger.info(f"📁 Documents path: {documents_path}")
        logger.info(f"📁 Found {len(list(documents_path.iterdir()))} items in documents folder")
        
        # Ingest documents
        logger.info("📥 Starting document ingestion...")
        success = await rag_system.ingest_documents(str(documents_path))
        
        if success:
            logger.info("✅ Document ingestion completed successfully!")
            
            # Test retrieval
            logger.info("🧪 Testing document retrieval...")
            from core.schemas import ConversationContext, KnowledgeLevel
            from datetime import datetime
            
            test_context = ConversationContext(
                session_id="test_ingestion",
                knowledge_level=KnowledgeLevel.BEGINNER,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            test_query = "What is life insurance?"
            result = await rag_system.get_semantic_response(test_query, test_context)
            
            logger.info(f"📄 Test query: '{test_query}'")
            logger.info(f"📄 Response length: {len(result.response)} characters")
            logger.info(f"📄 Quality score: {result.quality_score}")
            logger.info(f"📄 Confidence: {result.confidence}")
            logger.info(f"📄 Source documents: {len(result.source_documents)}")
            
            if result.source_documents:
                logger.info("📄 Source document sources:")
                for i, doc in enumerate(result.source_documents[:3]):  # Show first 3
                    source = doc.get('metadata', {}).get('source', 'Unknown')
                    logger.info(f"  {i+1}. {source}")
            
            logger.info("✅ Document ingestion and testing completed successfully!")
            return True
        else:
            logger.error("❌ Document ingestion failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)