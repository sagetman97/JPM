"""
Contextual Compression with Reranking Implementation

Uses Cohere reranker to improve retrieval quality by reranking documents based on relevance.
Based on patterns from AIE7 Advanced Retrieval course materials.
"""

from typing import List, Dict, Any, Optional
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
import cohere
from operator import itemgetter

from config.settings import settings

class EnhancedContextualCompressionRetriever(BaseRetriever):
    """
    Enhanced contextual compression retriever with Cohere reranking.
    
    This implementation follows the pattern from AIE7 Advanced Retrieval course,
    using Cohere's reranker to improve retrieval quality.
    """
    
    def __init__(
        self,
        base_retriever: BaseRetriever,
        cohere_api_key: str,
        top_n: int = 10,
        rerank_top_k: int = 4,
        model: str = "rerank-english-v2.0"
    ):
        """
        Initialize enhanced contextual compression retriever.
        
        Args:
            base_retriever: Base retriever to use for initial retrieval
            cohere_api_key: Cohere API key for reranking
            top_n: Number of documents to retrieve initially
            rerank_top_k: Number of documents to return after reranking
            model: Cohere rerank model to use
        """
        self.base_retriever = base_retriever
        self.top_n = top_n
        self.rerank_top_k = rerank_top_k
        self.model = model
        
        # Initialize Cohere client
        self.cohere_client = cohere.Client(cohere_api_key)
        
        # Create compressor with Cohere reranker
        self.compressor = CohereRerank(
            cohere_api_key=cohere_api_key,
            model=model,
            top_n=rerank_top_k
        )
        
        # Create contextual compression retriever
        self.compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=base_retriever
        )
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Retrieve documents using contextual compression with reranking.
        
        Args:
            query: Search query
            run: Callback manager
            
        Returns:
            List of relevant documents
        """
        try:
            # Use the compression retriever
            documents = self.compression_retriever.get_relevant_documents(query)
            return documents
        except Exception as e:
            print(f"Error in contextual compression retrieval: {e}")
            # Fallback to base retriever
            return self.base_retriever.get_relevant_documents(query)
    
    def _rerank_documents(
        self, 
        query: str, 
        documents: List[Document]
    ) -> List[Document]:
        """
        Rerank documents using Cohere reranker.
        
        Args:
            query: Search query
            documents: List of documents to rerank
            
        Returns:
            Reranked documents
        """
        try:
            # Prepare documents for reranking
            texts = [doc.page_content for doc in documents]
            
            # Rerank using Cohere
            response = self.cohere_client.rerank(
                query=query,
                documents=texts,
                model=self.model,
                top_n=self.rerank_top_k
            )
            
            # Reconstruct documents with reranked order
            reranked_docs = []
            for result in response.results:
                doc_index = result.index
                if doc_index < len(documents):
                    reranked_docs.append(documents[doc_index])
            
            return reranked_docs
            
        except Exception as e:
            print(f"Error in reranking: {e}")
            return documents[:self.rerank_top_k]
    
    def get_retrieval_analysis(self, query: str) -> Dict[str, Any]:
        """
        Get analysis of retrieval and reranking performance.
        
        Args:
            query: Search query
            
        Returns:
            Retrieval analysis statistics
        """
        try:
            # Get initial documents
            initial_docs = self.base_retriever.get_relevant_documents(query)
            
            # Rerank documents
            reranked_docs = self._rerank_documents(query, initial_docs)
            
            # Calculate statistics
            analysis = {
                "query": query,
                "initial_document_count": len(initial_docs),
                "reranked_document_count": len(reranked_docs),
                "compression_ratio": len(reranked_docs) / len(initial_docs) if initial_docs else 0,
                "initial_documents": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    } for doc in initial_docs[:5]
                ],
                "reranked_documents": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    } for doc in reranked_docs
                ]
            }
            
            return analysis
            
        except Exception as e:
            return {
                "query": query,
                "error": str(e)
            }
    
    def add_documents(self, documents: List[Document]):
        """
        Add new documents to the base retriever.
        
        Args:
            documents: New documents to add
        """
        if hasattr(self.base_retriever, 'add_documents'):
            self.base_retriever.add_documents(documents)
    
    def get_reranking_stats(self, query: str, documents: List[Document]) -> Dict[str, Any]:
        """
        Get detailed reranking statistics.
        
        Args:
            query: Search query
            documents: Documents to analyze
            
        Returns:
            Reranking statistics
        """
        try:
            # Get reranking scores
            texts = [doc.page_content for doc in documents]
            
            response = self.cohere_client.rerank(
                query=query,
                documents=texts,
                model=self.model,
                top_n=len(documents)
            )
            
            # Analyze scores
            scores = [result.relevance_score for result in response.results]
            
            return {
                "query": query,
                "document_count": len(documents),
                "average_score": sum(scores) / len(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "score_distribution": {
                    "high": len([s for s in scores if s > 0.8]),
                    "medium": len([s for s in scores if 0.5 <= s <= 0.8]),
                    "low": len([s for s in scores if s < 0.5])
                },
                "top_documents": [
                    {
                        "index": result.index,
                        "score": result.relevance_score,
                        "content": documents[result.index].page_content[:100] + "..."
                    } for result in response.results[:3]
                ]
            }
            
        except Exception as e:
            return {
                "query": query,
                "error": str(e)
            } 