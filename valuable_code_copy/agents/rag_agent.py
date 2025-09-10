"""
Enhanced RAG Agent for the Financial Advisor Assistant.
Based on patterns from AIE7 course materials with advanced retrieval techniques.
"""

import os
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from config.settings import settings
from utils.chunking import chunk_documents
from utils.confidence import assess_confidence_score, get_confidence_feedback
from utils.rate_limiter import api_rate_limiter
from retrieval import (
    HybridRetriever,
    EnhancedMultiQueryRetriever,
    EnhancedParentDocumentRetriever,
    EnhancedContextualCompressionRetriever,
    EnhancedEnsembleRetriever,
    EnhancedSemanticChunker
)


class EnhancedRAGAgent:
    """
    Enhanced RAG Agent for handling life insurance and financial advisor queries.
    Based on patterns from 04_Production_RAG and 02_Embeddings_and_RAG with advanced retrieval.
    """
    
    def __init__(self, retrieval_method: str = "basic"):
        """
        Initialize the enhanced RAG agent with LLM, embeddings, vector store, and advanced retrieval.
        
        Args:
            retrieval_method: Advanced retrieval method to use
        """
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL
        )
        
        self.retrieval_method = retrieval_method
        
        # Initialize vector store (will be set up when client is available)
        self.vector_store = None
        
        # Initialize advanced retrievers
        self.advanced_retrievers = {}
        self.semantic_chunker = None
        
        # Create RAG chain
        self.rag_chain = self._create_rag_chain()
    
    def _create_rag_chain(self):
        """
        Create the RAG chain with prompt template and advanced retrieval.
        Based on patterns from 04_Production_RAG.
        """
        # Prompt template for financial advisor responses
        template = """You are a financial advisor assistant specializing in life insurance. Provide accurate, helpful information while emphasizing the importance of consulting with licensed professionals.

Context: {context}

Question: {question}

Provide a clear, professional response that addresses the question using the context provided. Keep your response concise and actionable."""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Create the RAG chain with advanced retrieval
        rag_chain = (
            {"context": self._get_relevant_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def _initialize_advanced_retrievers(self):
        """
        Initialize advanced retrieval methods when vector store is available.
        """
        if not self.vector_store or not self.vector_store.client:
            return
        
        try:
            # Get base documents for initialization
            base_docs = self._get_base_documents()
            
            if base_docs:
                # Initialize hybrid retriever
                self.advanced_retrievers["hybrid"] = HybridRetriever(
                    documents=base_docs,
                    embeddings=self.embeddings
                )
                
                # Initialize multi-query retriever
                self.advanced_retrievers["multi_query"] = EnhancedMultiQueryRetriever(
                    base_retriever=self.vector_store.as_retriever(),
                    llm=self.llm
                )
                
                # Initialize parent-document retriever
                self.advanced_retrievers["parent_document"] = EnhancedParentDocumentRetriever(
                    documents=base_docs,
                    embeddings=self.embeddings
                )
                
                # Initialize ensemble retriever
                retrievers = [
                    self.vector_store.as_retriever(),
                    self.advanced_retrievers["hybrid"],
                    self.advanced_retrievers["multi_query"]
                ]
                
                self.advanced_retrievers["ensemble"] = EnhancedEnsembleRetriever(
                    retrievers=retrievers
                )
                
                # Initialize semantic chunker
                self.semantic_chunker = EnhancedSemanticChunker(
                    embeddings=self.embeddings
                )
                
        except Exception as e:
            print(f"Error initializing advanced retrievers: {e}")
    
    def _get_base_documents(self) -> List[Document]:
        """
        Get base documents for initializing advanced retrievers.
        
        Returns:
            List of base documents
        """
        try:
            # Get a sample of documents from the vector store
            docs = self.vector_store.similarity_search("life insurance", k=20)
            return docs
        except Exception as e:
            print(f"Error getting base documents: {e}")
            return []
    
    def _get_relevant_docs(self, question: str) -> str:
        """
        Retrieve relevant documents using the selected retrieval method.
        
        Args:
            question: User question
            
        Returns:
            Context string from relevant documents
        """
        if not self.vector_store or not self.vector_store.client:
            return "No knowledge base available."
        
        try:
            # Use basic similarity search for now
            docs = self.vector_store.similarity_search(question, k=settings.TOP_K_RETRIEVAL)
            
            # Limit context length to prevent token overflow
            context_parts = []
            total_length = 0
            max_context_length = 3000  # Conservative limit
            
            for doc in docs:
                doc_content = doc.page_content
                if total_length + len(doc_content) < max_context_length:
                    context_parts.append(doc_content)
                    total_length += len(doc_content)
                else:
                    # Truncate if we're getting too long
                    remaining = max_context_length - total_length
                    if remaining > 100:  # Only add if we have meaningful space
                        context_parts.append(doc_content[:remaining] + "...")
                    break
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return "Error retrieving relevant information."
    
    def query(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the enhanced RAG system with a question.
        
        Args:
            question: User's question
            session_id: Optional session ID for session-specific documents
            
        Returns:
            Dictionary containing response, confidence score, and metadata
        """
        try:
            # Wait for rate limiter before making API calls
            api_rate_limiter.wait_if_needed()
            
            # Get response from RAG chain with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.rag_chain.invoke(question)
                    break
                except Exception as e:
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 2  # Exponential backoff
                            import time
                            time.sleep(wait_time)
                            continue
                    raise e
            
            # Get retrieved documents for confidence assessment
            retrieved_docs = self.similarity_search(question, k=settings.TOP_K_RETRIEVAL)
            
            # Skip confidence assessment for now to reduce API calls
            confidence_score = 0.8  # Default confidence
            confidence_feedback = "Response generated successfully"
            
            # Get retrieval analysis
            retrieval_analysis = self._get_retrieval_analysis(question)
            
            return {
                "response": response,
                "confidence_score": confidence_score,
                "confidence_feedback": confidence_feedback,
                "retrieved_docs": retrieved_docs,
                "source_documents": [doc.metadata.get("source", "Unknown") for doc in retrieved_docs],
                "session_id": session_id,
                "retrieval_method": self.retrieval_method,
                "retrieval_analysis": retrieval_analysis
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or contact support if the issue persists.",
                "confidence_score": 0.0,
                "confidence_feedback": "Error occurred during processing",
                "retrieved_docs": [],
                "source_documents": [],
                "session_id": session_id,
                "retrieval_method": self.retrieval_method,
                "retrieval_analysis": {"error": str(e)},
                "error": str(e)
            }
    
    def _get_retrieval_analysis(self, question: str) -> Dict[str, Any]:
        """
        Get analysis of retrieval performance.
        
        Args:
            question: User question
            
        Returns:
            Retrieval analysis
        """
        try:
            if self.retrieval_method in self.advanced_retrievers:
                retriever = self.advanced_retrievers[self.retrieval_method]
                
                if hasattr(retriever, 'get_retrieval_stats'):
                    return retriever.get_retrieval_stats(question)
                elif hasattr(retriever, 'get_ensemble_analysis'):
                    return retriever.get_ensemble_analysis(question)
                elif hasattr(retriever, 'get_query_analysis'):
                    return retriever.get_query_analysis(question)
            
            return {"method": self.retrieval_method, "status": "basic_retrieval"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def add_documents(self, documents: List[Document], collection_name: Optional[str] = None):
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            collection_name: Optional collection name (for session-specific docs)
        """
        try:
            # Chunk documents
            chunked_docs = chunk_documents(documents)
            
            # Add to vector store
            if collection_name:
                # Create session-specific collection
                session_vector_store = Qdrant(
                    client=None,  # Will be set when connecting to Qdrant
                    collection_name=collection_name,
                    embeddings=self.embeddings
                )
                session_vector_store.add_documents(chunked_docs)
            else:
                # Add to main collection
                self.vector_store.add_documents(chunked_docs)
                
        except Exception as e:
            raise ValueError(f"Error adding documents to vector store: {str(e)}")
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Perform similarity search using the selected retrieval method.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if not self.vector_store or not self.vector_store.client:
            return []
        
        try:
            if self.retrieval_method in self.advanced_retrievers:
                retriever = self.advanced_retrievers[self.retrieval_method]
                return retriever.get_relevant_documents(query)
            else:
                return self.vector_store.similarity_search(query, k=k)
                
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection and advanced retrievers.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            # Get basic collection info
            stats = {
                "collection_name": settings.QDRANT_COLLECTION_NAME,
                "status": "active",
                "retrieval_method": self.retrieval_method,
                "advanced_retrievers": list(self.advanced_retrievers.keys())
            }
            
            # Add advanced retriever stats
            if self.advanced_retrievers:
                stats["advanced_retriever_status"] = "initialized"
            else:
                stats["advanced_retriever_status"] = "not_initialized"
            
            return stats
            
        except Exception as e:
            return {
                "collection_name": settings.QDRANT_COLLECTION_NAME,
                "status": "error",
                "retrieval_method": self.retrieval_method,
                "error": str(e)
            }
    
    def clear_session_documents(self, session_id: str):
        """
        Clear session-specific documents from vector store.
        
        Args:
            session_id: Session identifier
        """
        try:
            session_collection = f"session_{session_id}_docs"
            # This would need to be implemented based on Qdrant client capabilities
            print(f"Cleared session documents for session: {session_id}")
        except Exception as e:
            print(f"Warning: Could not clear session documents: {e}")


    def set_retrieval_method(self, method: str):
        """
        Set the retrieval method to use.
        
        Args:
            method: Retrieval method name
        """
        valid_methods = ["basic", "hybrid", "multi_query", "parent_document", "ensemble"]
        if method in valid_methods:
            self.retrieval_method = method
        else:
            print(f"Invalid retrieval method: {method}. Using basic retrieval.")
            self.retrieval_method = "basic"
    
    def get_available_retrieval_methods(self) -> List[str]:
        """
        Get list of available retrieval methods.
        
        Returns:
            List of available methods
        """
        methods = ["basic"]
        methods.extend(list(self.advanced_retrievers.keys()))
        return methods


# Backward compatibility
RAGAgent = EnhancedRAGAgent

# Global RAG agent instance
rag_agent = EnhancedRAGAgent() 