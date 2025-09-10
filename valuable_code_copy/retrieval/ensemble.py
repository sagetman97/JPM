"""
Ensemble Retrieval Implementation

Combines multiple retrievers using reciprocal rank fusion for improved performance.
Based on patterns from AIE7 Advanced Retrieval course materials.
"""

from typing import List, Dict, Any, Optional
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from operator import itemgetter
import numpy as np

from config.settings import settings

class EnhancedEnsembleRetriever(BaseRetriever):
    """
    Enhanced ensemble retriever with custom weighting and analysis.
    
    This implementation follows the pattern from AIE7 Advanced Retrieval course,
    combining multiple retrievers using reciprocal rank fusion.
    """
    
    def __init__(
        self,
        retrievers: List[BaseRetriever],
        weights: Optional[List[float]] = None,
        k: int = 4
    ):
        """
        Initialize enhanced ensemble retriever.
        
        Args:
            retrievers: List of retrievers to combine
            weights: Optional weights for each retriever (default: equal weights)
            k: Number of documents to return
        """
        self.retrievers = retrievers
        self.k = k
        
        # Set default weights if not provided
        if weights is None:
            self.weights = [1.0 / len(retrievers)] * len(retrievers)
        else:
            # Normalize weights
            total_weight = sum(weights)
            self.weights = [w / total_weight for w in weights]
        
        # Create ensemble retriever
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=retrievers,
            weights=self.weights
        )
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Retrieve documents using ensemble approach.
        
        Args:
            query: Search query
            run: Callback manager
            
        Returns:
            List of relevant documents
        """
        try:
            # Use ensemble retriever
            documents = self.ensemble_retriever.get_relevant_documents(query)
            return documents[:self.k]
        except Exception as e:
            print(f"Error in ensemble retrieval: {e}")
            # Fallback to first retriever
            return self.retrievers[0].get_relevant_documents(query)[:self.k]
    
    def _reciprocal_rank_fusion(
        self, 
        query: str, 
        documents: List[Document]
    ) -> List[Document]:
        """
        Apply reciprocal rank fusion to combine results.
        
        Args:
            query: Search query
            documents: List of documents to rank
            
        Returns:
            Reranked documents
        """
        # Get results from each retriever
        all_results = []
        
        for i, retriever in enumerate(self.retrievers):
            try:
                docs = retriever.get_relevant_documents(query)
                for j, doc in enumerate(docs):
                    all_results.append({
                        'doc': doc,
                        'retriever_index': i,
                        'rank': j + 1,
                        'weight': self.weights[i]
                    })
            except Exception as e:
                print(f"Error with retriever {i}: {e}")
                continue
        
        # Calculate RRF scores
        doc_scores = {}
        for result in all_results:
            doc_id = self._get_doc_id(result['doc'])
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'doc': result['doc'],
                    'score': 0.0,
                    'retrievers': []
                }
            
            # RRF formula: 1 / (k + rank)
            rrf_score = 1.0 / (60 + result['rank'])  # k=60 as per paper
            weighted_score = rrf_score * result['weight']
            
            doc_scores[doc_id]['score'] += weighted_score
            doc_scores[doc_id]['retrievers'].append(result['retriever_index'])
        
        # Sort by RRF score
        sorted_results = sorted(
            doc_scores.values(), 
            key=lambda x: x['score'], 
            reverse=True
        )
        
        return [result['doc'] for result in sorted_results[:self.k]]
    
    def _get_doc_id(self, doc: Document) -> str:
        """
        Generate a unique ID for a document.
        
        Args:
            doc: Document
            
        Returns:
            Document ID
        """
        return str(hash(doc.page_content))
    
    def get_ensemble_analysis(self, query: str) -> Dict[str, Any]:
        """
        Get analysis of ensemble retrieval performance.
        
        Args:
            query: Search query
            
        Returns:
            Ensemble analysis statistics
        """
        try:
            # Get results from each retriever
            retriever_results = {}
            all_docs = set()
            
            for i, retriever in enumerate(self.retrievers):
                try:
                    docs = retriever.get_relevant_documents(query)
                    retriever_results[f"retriever_{i}"] = {
                        "weight": self.weights[i],
                        "document_count": len(docs),
                        "documents": [doc.page_content[:100] + "..." for doc in docs[:3]],
                        "doc_ids": [self._get_doc_id(doc) for doc in docs]
                    }
                    
                    # Track all unique documents
                    for doc in docs:
                        all_docs.add(self._get_doc_id(doc))
                        
                except Exception as e:
                    retriever_results[f"retriever_{i}"] = {
                        "weight": self.weights[i],
                        "error": str(e)
                    }
            
            # Calculate ensemble statistics
            total_weight = sum(self.weights)
            weighted_doc_count = sum(
                result.get("document_count", 0) * result.get("weight", 0)
                for result in retriever_results.values()
                if "document_count" in result
            )
            
            # Calculate overlap statistics
            doc_retriever_map = {}
            for retriever_name, result in retriever_results.items():
                if "doc_ids" in result:
                    for doc_id in result["doc_ids"]:
                        if doc_id not in doc_retriever_map:
                            doc_retriever_map[doc_id] = []
                        doc_retriever_map[doc_id].append(retriever_name)
            
            overlap_stats = {
                "total_unique_docs": len(all_docs),
                "docs_found_by_multiple": len([d for d in doc_retriever_map.values() if len(d) > 1]),
                "average_retrievers_per_doc": sum(len(retrievers) for retrievers in doc_retriever_map.values()) / len(doc_retriever_map) if doc_retriever_map else 0
            }
            
            return {
                "query": query,
                "retriever_results": retriever_results,
                "overlap_stats": overlap_stats,
                "weighted_document_count": weighted_doc_count,
                "total_weight": total_weight,
                "ensemble_config": {
                    "retriever_count": len(self.retrievers),
                    "weights": self.weights,
                    "k": self.k
                }
            }
            
        except Exception as e:
            return {
                "query": query,
                "error": str(e)
            }
    
    def add_documents(self, documents: List[Document]):
        """
        Add new documents to all retrievers.
        
        Args:
            documents: New documents to add
        """
        for retriever in self.retrievers:
            if hasattr(retriever, 'add_documents'):
                retriever.add_documents(documents)
    
    def get_retriever_performance_comparison(self, query: str) -> Dict[str, Any]:
        """
        Compare performance of individual retrievers.
        
        Args:
            query: Search query
            
        Returns:
            Performance comparison statistics
        """
        try:
            comparison = {
                "query": query,
                "retriever_comparison": {}
            }
            
            for i, retriever in enumerate(self.retrievers):
                try:
                    # Time the retrieval
                    import time
                    start_time = time.time()
                    docs = retriever.get_relevant_documents(query)
                    end_time = time.time()
                    
                    comparison["retriever_comparison"][f"retriever_{i}"] = {
                        "weight": self.weights[i],
                        "document_count": len(docs),
                        "latency_ms": (end_time - start_time) * 1000,
                        "documents": [doc.page_content[:100] + "..." for doc in docs[:3]]
                    }
                    
                except Exception as e:
                    comparison["retriever_comparison"][f"retriever_{i}"] = {
                        "weight": self.weights[i],
                        "error": str(e)
                    }
            
            return comparison
            
        except Exception as e:
            return {
                "query": query,
                "error": str(e)
            } 