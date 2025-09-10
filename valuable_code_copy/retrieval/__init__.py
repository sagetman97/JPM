"""
Advanced Retrieval Techniques for Financial Advisor Assistant

This package implements various advanced retrieval methods including:
- Hybrid Search (BM25 + Semantic)
- Multi-Query Retrieval
- Parent-Document Retrieval
- Contextual Compression (Reranking)
- Ensemble Retrieval
- Semantic Chunking
"""

from .hybrid_search import HybridRetriever
from .multi_query import MultiQueryRetriever, EnhancedMultiQueryRetriever
from .parent_document import ParentDocumentRetriever, EnhancedParentDocumentRetriever
from .contextual_compression import ContextualCompressionRetriever, EnhancedContextualCompressionRetriever
from .ensemble import EnsembleRetriever, EnhancedEnsembleRetriever
from .semantic_chunking import SemanticChunker, EnhancedSemanticChunker

__all__ = [
    "HybridRetriever",
    "MultiQueryRetriever",
    "EnhancedMultiQueryRetriever",
    "ParentDocumentRetriever",
    "EnhancedParentDocumentRetriever",
    "ContextualCompressionRetriever",
    "EnhancedContextualCompressionRetriever",
    "EnsembleRetriever",
    "EnhancedEnsembleRetriever",
    "SemanticChunker",
    "EnhancedSemanticChunker"
] 