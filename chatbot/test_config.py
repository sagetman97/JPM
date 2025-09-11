#!/usr/bin/env python3
"""
Test script to verify configuration and Qdrant connection.
Run this to test the new environment-aware configuration.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the chatbot directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import config
from core.advanced_rag import EnhancedRAGSystem
from core.session_persistence import SessionPersistenceManager

async def test_configuration():
    """Test the new configuration system"""
    print("🔧 Testing RoboAdvisor Chatbot Configuration")
    print("=" * 50)
    
    # Test 1: Configuration
    print("\n1. Configuration Test:")
    print(f"   Environment: {'Production' if config.is_production else 'Localhost'}")
    print(f"   Qdrant Host: {config.qdrant_host}")
    print(f"   Qdrant Port: {config.qdrant_port}")
    print(f"   Qdrant HTTPS: {config.qdrant_https}")
    print(f"   RAG Documents Path: {config.rag_documents_path}")
    print(f"   RAG Documents Exists: {os.path.exists(config.rag_documents_path)}")
    
    # Test 2: RAG System
    print("\n2. RAG System Test:")
    try:
        rag_system = EnhancedRAGSystem()
        print(f"   ✅ RAG System initialized successfully")
        print(f"   Qdrant Available: {rag_system.qdrant_available}")
        
        # Test document ingestion
        if os.path.exists(config.rag_documents_path):
            print(f"   📁 Found {len(list(Path(config.rag_documents_path).iterdir()))} items in RAG Documents folder")
            
            # Check if documents are already ingested
            if rag_system.has_documents():
                collection_info = rag_system.collection_info
                if collection_info:
                    print(f"   📚 RAG database has {collection_info.vectors_count} documents")
                else:
                    print(f"   📚 RAG database has documents (count unknown)")
            else:
                print(f"   📥 RAG database is empty - would need document ingestion")
        else:
            print(f"   ❌ RAG Documents folder not found at: {config.rag_documents_path}")
            
    except Exception as e:
        print(f"   ❌ RAG System initialization failed: {e}")
    
    # Test 3: Session Persistence
    print("\n3. Session Persistence Test:")
    try:
        session_manager = SessionPersistenceManager(rag_system.qdrant_client if 'rag_system' in locals() else None)
        print(f"   ✅ Session Persistence initialized successfully")
        print(f"   Storage Type: {'Qdrant' if session_manager.use_qdrant else 'Memory'}")
        
        # Test session stats
        stats = session_manager.get_session_stats()
        print(f"   Session Stats: {stats}")
        
    except Exception as e:
        print(f"   ❌ Session Persistence initialization failed: {e}")
    
    # Test 4: Environment Variables
    print("\n4. Environment Variables Test:")
    env_vars = [
        'OPENAI_API_KEY',
        'QDRANT_HOST', 
        'QDRANT_PORT',
        'QDRANT_HTTPS',
        'QDRANT_API_KEY',
        'BACKEND_API_URL'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'NOT_SET')
        if var == 'OPENAI_API_KEY' and value != 'NOT_SET':
            value = f"{value[:8]}..." if len(value) > 8 else "SET"
        elif var == 'QDRANT_API_KEY' and value != 'NOT_SET':
            value = f"{value[:8]}..." if len(value) > 8 else "SET"
        print(f"   {var}: {value}")
    
    print("\n" + "=" * 50)
    print("✅ Configuration test completed!")

if __name__ == "__main__":
    asyncio.run(test_configuration())
