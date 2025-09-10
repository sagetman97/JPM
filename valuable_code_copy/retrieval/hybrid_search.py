"""
Hybrid Search Implementation

Combines BM25 (keyword-based) and semantic search for improved retrieval performance.
Based on patterns from AIE7 Advanced Retrieval course materials.
"""

from typing import List, Dict, Any, Optional
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
import numpy as np
from operator import itemgetter

from config.settings import settings

class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever that combines BM25 and semantic search.
    
    This implementation follows the pattern from AIE7 Advanced Retrieval course,
    combining keyword-based (BM25) and semantic search for improved performance.
    """
    
    def __init__(
        self,
        documents: List[Document],
        embeddings: OpenAIEmbeddings,
        k: int = 4,
        bm25_weight: float = 0.5,
        semantic_weight: float = 0.5
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            documents: List of documents to index
            embeddings: Embeddings model for semantic search
            k: Number of documents to retrieve
            bm25_weight: Weight for BM25 scores
            semantic_weight: Weight for semantic search scores
        """
        self.k = k
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        
        # Initialize BM25 retriever
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        
        # Initialize semantic retriever (Qdrant)
        self.vectorstore = Qdrant.from_documents(
            documents,
            embeddings,
            location=":memory:",
            collection_name="hybrid_search"
        )
        self.semantic_retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": k * 2}  # Get more candidates for reranking
        )
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Retrieve documents using hybrid search.
        
        Args:
            query: Search query
            run: Callback manager
            
        Returns:
            List of relevant documents
        """
        # Get BM25 results
        bm25_docs = self.bm25_retriever.get_relevant_documents(query)
        bm25_scores = self.bm25_retriever.get_relevant_documents_with_scores(query)
        
        # Get semantic search results
        semantic_docs = self.semantic_retriever.get_relevant_documents(query)
        semantic_scores = self.semantic_retriever.get_relevant_documents_with_scores(query)
        
        # Combine and rerank results
        combined_results = self._combine_results(
            bm25_scores, 
            semantic_scores, 
            query
        )
        
        # Return top k documents
        return [doc for doc, score in combined_results[:self.k]]
    
    def _combine_results(
        self, 
        bm25_scores: List[tuple], 
        semantic_scores: List[tuple], 
        query: str
    ) -> List[tuple]:
        """
        Combine BM25 and semantic search results using weighted scoring.
        
        Args:
            bm25_scores: BM25 results with scores
            semantic_scores: Semantic search results with scores
            query: Original query
            
        Returns:
            Combined and reranked results
        """
        # Create document ID to score mapping
        doc_scores = {}
        
        # Add BM25 scores
        for doc, score in bm25_scores:
            doc_id = self._get_doc_id(doc)
            doc_scores[doc_id] = {
                'doc': doc,
                'bm25_score': score,
                'semantic_score': 0.0
            }
        
        # Add semantic search scores
        for doc, score in semantic_scores:
            doc_id = self._get_doc_id(doc)
            if doc_id in doc_scores:
                doc_scores[doc_id]['semantic_score'] = score
            else:
                doc_scores[doc_id] = {
                    'doc': doc,
                    'bm25_score': 0.0,
                    'semantic_score': score
                }
        
        # Calculate combined scores
        combined_results = []
        for doc_id, scores in doc_scores.items():
            combined_score = (
                self.bm25_weight * scores['bm25_score'] +
                self.semantic_weight * scores['semantic_score']
            )
            combined_results.append((scores['doc'], combined_score))
        
        # Sort by combined score (descending)
        combined_results.sort(key=itemgetter(1), reverse=True)
        
        return combined_results
    
    def _get_doc_id(self, doc: Document) -> str:
        """
        Generate a unique ID for a document.
        
        Args:
            doc: Document
            
        Returns:
            Document ID
        """
        # Use content hash as ID
        return str(hash(doc.page_content))
    
    def add_documents(self, documents: List[Document]):
        """
        Add new documents to the hybrid retriever.
        
        Args:
            documents: New documents to add
        """
        # Add to BM25 retriever
        self.bm25_retriever.add_documents(documents)
        
        # Add to vector store
        self.vectorstore.add_documents(documents)
    
    def get_retrieval_stats(self, query: str) -> Dict[str, Any]:
        """
        Get retrieval statistics for analysis.
        
        Args:
            query: Search query
            
        Returns:
            Retrieval statistics
        """
        bm25_docs = self.bm25_retriever.get_relevant_documents(query)
        semantic_docs = self.semantic_retriever.get_relevant_documents(query)
        
        # Calculate overlap
        bm25_ids = {self._get_doc_id(doc) for doc in bm25_docs}
        semantic_ids = {self._get_doc_id(doc) for doc in semantic_docs}
        overlap = len(bm25_ids.intersection(semantic_ids))
        
        return {
            "bm25_docs_count": len(bm25_docs),
            "semantic_docs_count": len(semantic_docs),
            "overlap_count": overlap,
            "overlap_percentage": overlap / max(len(bm25_docs), len(semantic_docs)) if max(len(bm25_docs), len(semantic_docs)) > 0 else 0,
            "bm25_weight": self.bm25_weight,
            "semantic_weight": self.semantic_weight
        } 