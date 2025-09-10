"""
Semantic Chunking Implementation

Advanced document chunking based on semantic similarity for better context preservation.
Based on patterns from AIE7 Advanced Retrieval course materials.
"""

from typing import List, Dict, Any, Optional
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
import numpy as np

from config.settings import settings

class EnhancedSemanticChunker:
    """
    Enhanced semantic chunker with custom configuration.
    
    This implementation follows the pattern from AIE7 Advanced Retrieval course,
    providing advanced document chunking based on semantic similarity.
    """
    
    def __init__(
        self,
        embeddings: OpenAIEmbeddings,
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_value: float = 0.95,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000
    ):
        """
        Initialize enhanced semantic chunker.
        
        Args:
            embeddings: Embeddings model for semantic analysis
            breakpoint_threshold_type: Type of threshold (percentile, standard_deviation, interquartile, gradient)
            breakpoint_threshold_value: Threshold value for chunking
            min_chunk_size: Minimum chunk size
            max_chunk_size: Maximum chunk size
        """
        self.embeddings = embeddings
        self.breakpoint_threshold_type = breakpoint_threshold_type
        self.breakpoint_threshold_value = breakpoint_threshold_value
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Create semantic chunker
        self.semantic_chunker = SemanticChunker(
            embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type,
            breakpoint_threshold_value=breakpoint_threshold_value
        )
    
    def split_documents(
        self, 
        documents: List[Document]
    ) -> List[Document]:
        """
        Split documents using semantic chunking.
        
        Args:
            documents: Documents to split
            
        Returns:
            List of semantically chunked documents
        """
        try:
            # Split documents using semantic chunker
            chunked_docs = self.semantic_chunker.split_documents(documents)
            
            # Apply size constraints
            filtered_docs = []
            for doc in chunked_docs:
                content_length = len(doc.page_content)
                if self.min_chunk_size <= content_length <= self.max_chunk_size:
                    filtered_docs.append(doc)
                elif content_length > self.max_chunk_size:
                    # Further split large chunks
                    sub_chunks = self._split_large_chunk(doc)
                    filtered_docs.extend(sub_chunks)
            
            return filtered_docs
            
        except Exception as e:
            print(f"Error in semantic chunking: {e}")
            return documents
    
    def _split_large_chunk(self, document: Document) -> List[Document]:
        """
        Split large chunks into smaller pieces.
        
        Args:
            document: Large document to split
            
        Returns:
            List of smaller documents
        """
        try:
            content = document.page_content
            words = content.split()
            
            chunks = []
            current_chunk = []
            current_size = 0
            
            for word in words:
                current_chunk.append(word)
                current_size += len(word) + 1  # +1 for space
                
                if current_size >= self.max_chunk_size:
                    # Create chunk
                    chunk_text = " ".join(current_chunk)
                    chunk_doc = Document(
                        page_content=chunk_text,
                        metadata=document.metadata.copy()
                    )
                    chunks.append(chunk_doc)
                    
                    # Reset for next chunk
                    current_chunk = []
                    current_size = 0
            
            # Add remaining content
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata=document.metadata.copy()
                )
                chunks.append(chunk_doc)
            
            return chunks
            
        except Exception as e:
            print(f"Error splitting large chunk: {e}")
            return [document]
    
    def analyze_chunking_quality(
        self, 
        original_docs: List[Document], 
        chunked_docs: List[Document]
    ) -> Dict[str, Any]:
        """
        Analyze the quality of semantic chunking.
        
        Args:
            original_docs: Original documents
            chunked_docs: Chunked documents
            
        Returns:
            Chunking quality analysis
        """
        try:
            # Calculate statistics
            original_sizes = [len(doc.page_content) for doc in original_docs]
            chunked_sizes = [len(doc.page_content) for doc in chunked_docs]
            
            # Calculate semantic similarity between adjacent chunks
            similarities = []
            for i in range(len(chunked_docs) - 1):
                try:
                    # Get embeddings for adjacent chunks
                    emb1 = self.embeddings.embed_query(chunked_docs[i].page_content)
                    emb2 = self.embeddings.embed_query(chunked_docs[i + 1].page_content)
                    
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(emb1, emb2)
                    similarities.append(similarity)
                except Exception as e:
                    print(f"Error calculating similarity: {e}")
                    similarities.append(0.0)
            
            return {
                "original_document_count": len(original_docs),
                "chunked_document_count": len(chunked_docs),
                "average_original_size": sum(original_sizes) / len(original_sizes) if original_sizes else 0,
                "average_chunked_size": sum(chunked_sizes) / len(chunked_sizes) if chunked_sizes else 0,
                "min_chunk_size": min(chunked_sizes) if chunked_sizes else 0,
                "max_chunk_size": max(chunked_sizes) if chunked_sizes else 0,
                "average_semantic_similarity": sum(similarities) / len(similarities) if similarities else 0,
                "chunking_ratio": len(chunked_docs) / len(original_docs) if original_docs else 0,
                "threshold_type": self.breakpoint_threshold_type,
                "threshold_value": self.breakpoint_threshold_value
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def get_chunking_recommendations(
        self, 
        analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Get recommendations for improving chunking quality.
        
        Args:
            analysis: Chunking analysis results
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        avg_similarity = analysis.get("average_semantic_similarity", 0)
        chunking_ratio = analysis.get("chunking_ratio", 0)
        avg_chunk_size = analysis.get("average_chunked_size", 0)
        
        if avg_similarity < 0.3:
            recommendations.append("Consider increasing threshold value for better semantic separation")
        elif avg_similarity > 0.8:
            recommendations.append("Consider decreasing threshold value for more granular chunks")
        
        if chunking_ratio < 2:
            recommendations.append("Consider more aggressive chunking for better retrieval")
        elif chunking_ratio > 10:
            recommendations.append("Consider less aggressive chunking to preserve context")
        
        if avg_chunk_size < self.min_chunk_size:
            recommendations.append("Increase minimum chunk size to preserve more context")
        elif avg_chunk_size > self.max_chunk_size:
            recommendations.append("Decrease maximum chunk size for better retrieval precision")
        
        return recommendations 