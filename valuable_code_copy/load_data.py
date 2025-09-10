"""
Data loading script for the Financial Advisor Assistant.
Loads life insurance documents into the vector store.
Based on patterns from AIE7 course materials.
"""

import os
import glob
from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    DirectoryLoader
)
from qdrant_client import QdrantClient
from config.settings import settings
from agents.rag_agent import rag_agent
from utils.chunking import chunk_documents


def load_life_insurance_documents() -> List[Document]:
    """
    Load all life insurance documents from the RAG Documents folder.
    Based on patterns from AIE7 course materials.
    """
    documents = []
    
    # Path to RAG Documents folder
    rag_docs_path = "../RAG Documents"
    
    if not os.path.exists(rag_docs_path):
        print(f"Warning: RAG Documents folder not found at {rag_docs_path}")
        return documents
    
    # Load text files
    txt_files = glob.glob(os.path.join(rag_docs_path, "*.txt"))
    for txt_file in txt_files:
        try:
            loader = TextLoader(txt_file, encoding='utf-8')
            docs = loader.load()
            
            # Add metadata
            for doc in docs:
                doc.metadata.update({
                    "source": os.path.basename(txt_file),
                    "file_type": "text",
                    "source_type": "life_insurance_doc"
                })
            
            documents.extend(docs)
            print(f"Loaded text file: {os.path.basename(txt_file)}")
            
        except Exception as e:
            print(f"Error loading {txt_file}: {e}")
    
    # Load PDF files
    pdf_files = glob.glob(os.path.join(rag_docs_path, "*.pdf"))
    for pdf_file in pdf_files:
        try:
            loader = PyMuPDFLoader(pdf_file)
            docs = loader.load()
            
            # Add metadata
            for doc in docs:
                doc.metadata.update({
                    "source": os.path.basename(pdf_file),
                    "file_type": "pdf",
                    "source_type": "life_insurance_doc"
                })
            
            documents.extend(docs)
            print(f"Loaded PDF file: {os.path.basename(pdf_file)}")
            
        except Exception as e:
            print(f"Error loading {pdf_file}: {e}")
    
    # Load markdown files
    md_files = glob.glob(os.path.join(rag_docs_path, "*.md"))
    for md_file in md_files:
        try:
            loader = TextLoader(md_file, encoding='utf-8')
            docs = loader.load()
            
            # Add metadata
            for doc in docs:
                doc.metadata.update({
                    "source": os.path.basename(md_file),
                    "file_type": "markdown",
                    "source_type": "life_insurance_doc"
                })
            
            documents.extend(docs)
            print(f"Loaded markdown file: {os.path.basename(md_file)}")
            
        except Exception as e:
            print(f"Error loading {md_file}: {e}")
    
    print(f"Total documents loaded: {len(documents)}")
    return documents


def initialize_vector_store():
    """
    Initialize the vector store with life insurance documents.
    Based on patterns from AIE7 course materials.
    """
    print("🚀 Initializing Financial Advisor Assistant...")
    
    # Validate settings
    try:
        settings.validate()
        print("✅ Settings validated successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Initialize Qdrant client
    try:
        qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        
        # Test connection
        collections = qdrant_client.get_collections()
        print(f"✅ Connected to Qdrant. Found {len(collections.collections)} collections")
        
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        print("Please ensure Qdrant is running on the specified host and port")
        return False
    
    # Load documents
    print("📚 Loading life insurance documents...")
    documents = load_life_insurance_documents()
    
    if not documents:
        print("❌ No documents loaded. Please check the RAG Documents folder.")
        return False
    
    # Chunk documents
    print("✂️ Chunking documents...")
    chunked_docs = chunk_documents(documents)
    print(f"✅ Created {len(chunked_docs)} chunks from {len(documents)} documents")
    
    # Add to vector store
    try:
        print("💾 Adding documents to vector store...")
        from langchain_qdrant import QdrantVectorStore
        from langchain_openai import OpenAIEmbeddings
        
        # Initialize vector store
        embeddings = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL)
        
        # Create collection if it doesn't exist
        try:
            qdrant_client.get_collection(settings.QDRANT_COLLECTION_NAME)
            print(f"✅ Collection '{settings.QDRANT_COLLECTION_NAME}' already exists")
        except Exception:
            print(f"📝 Creating collection '{settings.QDRANT_COLLECTION_NAME}'...")
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config={
                    "text": {
                        "size": 1536,  # OpenAI embedding size
                        "distance": "Cosine"
                    }
                }
            )
            print(f"✅ Collection '{settings.QDRANT_COLLECTION_NAME}' created successfully")
        
        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            embedding=embeddings,
            vector_name="text"
        )
        
        # Add documents to vector store
        vector_store.add_documents(chunked_docs)
        print("✅ Documents successfully added to vector store")
        
        # Get collection stats
        stats = rag_agent.get_collection_stats()
        print(f"📊 Collection status: {stats['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding documents to vector store: {e}")
        return False


def test_rag_system():
    """
    Test the RAG system with sample queries.
    """
    print("\n🧪 Testing RAG system with sample queries...")
    
    test_queries = [
        "What is the difference between term and whole life insurance?",
        "How does life insurance fit into a diversified portfolio?",
        "What are the tax implications of universal life insurance?",
        "How much life insurance coverage should I recommend?",
        "What are the benefits of indexed universal life insurance?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: {query}")
        try:
            result = rag_agent.query(query)
            print(f"✅ Response generated (confidence: {result['confidence_score']:.2f})")
            print(f"📄 Sources: {len(result['source_documents'])} documents")
        except Exception as e:
            print(f"❌ Error testing query: {e}")


if __name__ == "__main__":
    print("🏦 Financial Advisor Life Insurance Assistant - Data Loading")
    print("=" * 60)
    
    # Initialize vector store
    success = initialize_vector_store()
    
    if success:
        print("\n🎉 Initialization completed successfully!")
        
        # Test the system
        test_rag_system()
        
        print("\n🚀 Ready to start the application!")
        print("Run: chainlit run app.py")
    else:
        print("\n❌ Initialization failed. Please check the configuration and try again.") 