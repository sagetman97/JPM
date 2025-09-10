"""
Parent-Document Retrieval Implementation

Handles large documents by splitting into parent and child chunks for better context preservation.
Based on patterns from AIE7 Advanced Retrieval course materials.
"""

from typing import List, Dict, Any, Optional
from langchain.retrievers import ParentDocumentRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain.storage import InMemoryStore

from config.settings import settings

class EnhancedParentDocumentRetriever(BaseRetriever):
    """
    Enhanced parent-document retriever with custom configuration.
    
    This implementation follows the pattern from AIE7 Advanced Retrieval course,
    handling large documents with better context preservation.
    """
    
    def __init__(
        self,
        documents: List[Document],
        embeddings: OpenAIEmbeddings,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 400,
        child_chunk_overlap: int = 50,
        k: int = 4
    ):
        """
        Initialize enhanced parent-document retriever.
        
        Args:
            documents: Source documents
            embeddings: Embeddings model
            parent_chunk_size: Size of parent chunks
            child_chunk_size: Size of child chunks
            child_chunk_overlap: Overlap between child chunks
            k: Number of documents to return
        """
        self.k = k
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.child_chunk_overlap = child_chunk_overlap
        
        # Create text splitters
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=parent_chunk_size // 10
        )
        
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size,
            chunk_overlap=child_chunk_overlap
        )
        
        # Create vector store for parent documents
        self.parent_vectorstore = Qdrant.from_documents(
            documents,
            embeddings,
            location=":memory:",
            collection_name="parent_documents"
        )
        
        # Create document store
        self.docstore = InMemoryStore()
        
        # Create parent document retriever
        self.parent_retriever = ParentDocumentRetriever(
            vectorstore=self.parent_vectorstore,
            docstore=self.docstore,
            child_splitter=self.child_splitter,
            parent_splitter=self.parent_splitter
        )
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Retrieve documents using parent-document approach.
        
        Args:
            query: Search query
            run: Callback manager
            
        Returns:
            List of relevant documents
        """
        try:
            # Use parent document retriever
            documents = self.parent_retriever.get_relevant_documents(query)
            return documents[:self.k]
        except Exception as e:
            print(f"Error in parent document retrieval: {e}")
            return []
    
    def add_documents(self, documents: List[Document]):
        """
        Add new documents to the retriever.
        
        Args:
            documents: New documents to add
        """
        try:
            self.parent_retriever.add_documents(documents)
        except Exception as e:
            print(f"Error adding documents: {e}")
    
    def get_retrieval_stats(self, query: str) -> Dict[str, Any]:
        """
        Get retrieval statistics for analysis.
        
        Args:
            query: Search query
            
        Returns:
            Retrieval statistics
        """
        try:
            # Get documents
            docs = self.parent_retriever.get_relevant_documents(query)
            
            # Analyze document sizes
            doc_sizes = [len(doc.page_content) for doc in docs]
            
            return {
                "query": query,
                "document_count": len(docs),
                "average_document_size": sum(doc_sizes) / len(doc_sizes) if doc_sizes else 0,
                "min_document_size": min(doc_sizes) if doc_sizes else 0,
                "max_document_size": max(doc_sizes) if doc_sizes else 0,
                "parent_chunk_size": self.parent_chunk_size,
                "child_chunk_size": self.child_chunk_size,
                "child_chunk_overlap": self.child_chunk_overlap
            }
            
        except Exception as e:
            return {
                "query": query,
                "error": str(e)
            } 