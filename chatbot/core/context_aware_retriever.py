"""
Context-Aware Document Retriever

This module provides context-aware document retrieval that filters and ranks
documents based on conversation context and semantic relevance.
"""

import logging
from typing import List, Dict, Any, Optional
from .conversation_memory import ConversationMemory, MemoryType

logger = logging.getLogger(__name__)

class ContextAwareDocumentRetriever:
    """
    Context-aware document retriever that:
    - Filters documents based on conversation context
    - Ranks documents by context relevance
    - Ensures retrieved documents are contextually appropriate
    - Prevents retrieval of irrelevant documents
    """
    
    def __init__(self):
        self.context_relevance_threshold = 0.4
        self.max_context_documents = 5  # Maximum documents to retrieve based on context
        
    def filter_documents_by_context(self, documents: List[Dict[str, Any]], 
                                  conversation_memory: ConversationMemory,
                                  query: str) -> List[Dict[str, Any]]:
        """
        Filter documents based on conversation context relevance.
        
        Args:
            documents: List of documents from RAG retrieval
            conversation_memory: Current conversation memory
            query: Original user query
            
        Returns:
            Filtered and ranked documents with context relevance scores
        """
        try:
            if not documents:
                logger.info("🔍 CONTEXT RETRIEVER: No documents to filter")
                return []
            
            # Get conversation context
            context = conversation_memory.get_conversation_context()
            
            # Score documents by context relevance
            scored_documents = []
            for doc in documents:
                context_score = self._calculate_context_relevance(doc, context, query)
                doc['context_relevance'] = context_score
                scored_documents.append(doc)
            
            # Filter by context relevance threshold
            relevant_documents = [
                doc for doc in scored_documents 
                if doc.get('context_relevance', 0) >= self.context_relevance_threshold
            ]
            
            # If we have enough context-relevant documents, use them
            if len(relevant_documents) >= self.max_context_documents:
                # Sort by context relevance and original score
                relevant_documents.sort(
                    key=lambda x: (x.get('context_relevance', 0), x.get('score', 0)), 
                    reverse=True
                )
                final_documents = relevant_documents[:self.max_context_documents]
                logger.info(f"🔍 CONTEXT RETRIEVER: Using {len(final_documents)} context-relevant documents")
            else:
                # Mix context-relevant and high-scoring documents
                relevant_documents.sort(key=lambda x: x.get('context_relevance', 0), reverse=True)
                
                # Get remaining documents by original score
                remaining_docs = [doc for doc in scored_documents if doc not in relevant_documents]
                remaining_docs.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                # Combine and limit
                final_documents = relevant_documents + remaining_docs[:self.max_context_documents - len(relevant_documents)]
                logger.info(f"🔍 CONTEXT RETRIEVER: Using {len(relevant_documents)} context-relevant + {len(final_documents) - len(relevant_documents)} high-scoring documents")
            
            # Log context filtering results
            context_scores = [doc.get('context_relevance', 0) for doc in final_documents]
            avg_context_score = sum(context_scores) / len(context_scores) if context_scores else 0
            logger.info(f"🔍 CONTEXT RETRIEVER: Average context relevance: {avg_context_score:.3f}")
            
            return final_documents
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error filtering documents by context: {e}")
            return documents  # Return original documents on error
    
    def _calculate_context_relevance(self, document: Dict[str, Any], 
                                   context: Dict[str, Any], 
                                   query: str) -> float:
        """
        Calculate how relevant a document is to the current conversation context.
        
        Returns:
            Float between 0.0 and 1.0 representing context relevance
        """
        try:
            content = document.get('content', '').lower()
            source = document.get('source', '').lower()
            
            # Initialize relevance score
            relevance_score = 0.0
            context_factors = []
            
            # 1. Current topic relevance
            current_topic = context.get('current_topic', '').lower()
            if current_topic and self._check_topic_relevance(content, source, current_topic):
                relevance_score += 0.3
                context_factors.append(f"current_topic: {current_topic}")
            
            # 2. Recent topics relevance
            recent_topics = context.get('recent_topics', [])
            topic_relevance = self._check_topics_relevance(content, source, recent_topics)
            relevance_score += topic_relevance * 0.2
            if topic_relevance > 0:
                context_factors.append(f"recent_topics: {topic_relevance:.2f}")
            
            # 3. Recent concepts relevance
            recent_concepts = context.get('recent_concepts', [])
            concept_relevance = self._check_concepts_relevance(content, source, recent_concepts)
            relevance_score += concept_relevance * 0.2
            if concept_relevance > 0:
                context_factors.append(f"recent_concepts: {concept_relevance:.2f}")
            
            # 4. Query-context alignment
            query_context_alignment = self._check_query_context_alignment(content, source, query, context)
            relevance_score += query_context_alignment * 0.3
            if query_context_alignment > 0:
                context_factors.append(f"query_alignment: {query_context_alignment:.2f}")
            
            # Log context relevance calculation
            if context_factors:
                logger.debug(f"🔍 CONTEXT RETRIEVER: Document context relevance {relevance_score:.3f} - Factors: {', '.join(context_factors)}")
            
            return min(relevance_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error calculating context relevance: {e}")
            return 0.0
    
    def _check_topic_relevance(self, content: str, source: str, topic: str) -> bool:
        """Check if content is relevant to a specific topic"""
        try:
            topic_lower = topic.lower()
            
            # Check content relevance
            if topic_lower in content:
                return True
            
            # Check source relevance
            if topic_lower in source:
                return True
            
            # Check for topic variations
            topic_variations = self._get_topic_variations(topic_lower)
            for variation in topic_variations:
                if variation in content or variation in source:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error checking topic relevance: {e}")
            return False
    
    def _check_topics_relevance(self, content: str, source: str, topics: List[str]) -> float:
        """Check relevance to multiple topics and return average score"""
        try:
            if not topics:
                return 0.0
            
            relevance_scores = []
            for topic in topics:
                if self._check_topic_relevance(content, source, topic):
                    relevance_scores.append(1.0)
                else:
                    # Check for partial relevance
                    partial_score = self._calculate_partial_relevance(content, source, topic)
                    relevance_scores.append(partial_score)
            
            return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error checking topics relevance: {e}")
            return 0.0
    
    def _check_concepts_relevance(self, content: str, source: str, concepts: List[str]) -> float:
        """Check relevance to recent concepts"""
        try:
            if not concepts:
                return 0.0
            
            relevance_scores = []
            for concept in concepts:
                concept_lower = concept.lower()
                
                # Check for exact concept match
                if concept_lower in content or concept_lower in source:
                    relevance_scores.append(1.0)
                else:
                    # Check for concept-related terms
                    related_terms = self._get_concept_related_terms(concept_lower)
                    concept_score = 0.0
                    for term in related_terms:
                        if term in content or term in source:
                            concept_score = max(concept_score, 0.7)
                    
                    relevance_scores.append(concept_score)
            
            return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error checking concepts relevance: {e}")
            return 0.0
    
    def _check_query_context_alignment(self, content: str, source: str, 
                                     query: str, context: Dict[str, Any]) -> float:
        """Check how well the document aligns with the query in the current context"""
        try:
            query_lower = query.lower()
            current_topic = context.get('current_topic', '').lower()
            
            # If we have a current topic, check if the document bridges the topic and query
            if current_topic:
                # Check if document contains both topic and query terms
                topic_terms = current_topic.split()
                query_terms = query_lower.split()
                
                topic_present = any(term in content or term in source for term in topic_terms)
                query_present = any(term in content or term in source for term in query_terms)
                
                if topic_present and query_present:
                    return 0.9  # High alignment
                elif topic_present or query_present:
                    return 0.5  # Medium alignment
                else:
                    return 0.1  # Low alignment
            
            # If no current topic, just check query relevance
            query_terms = query_lower.split()
            query_present = any(term in content or term in source for term in query_terms)
            
            return 0.8 if query_present else 0.2
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error checking query context alignment: {e}")
            return 0.0
    
    def _get_topic_variations(self, topic: str) -> List[str]:
        """Get variations of a topic for better matching"""
        try:
            variations = [topic]
            
            # Common insurance topic variations
            if 'iul' in topic or 'indexed universal life' in topic:
                variations.extend(['iul', 'indexed universal life', 'index universal life'])
            elif 'universal life' in topic:
                variations.extend(['universal life', 'ul'])
            elif 'whole life' in topic:
                variations.extend(['whole life', 'wl'])
            elif 'term life' in topic:
                variations.extend(['term life', 'term'])
            
            return list(set(variations))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error getting topic variations: {e}")
            return [topic]
    
    def _get_concept_related_terms(self, concept: str) -> List[str]:
        """Get terms related to a concept for better matching"""
        try:
            related_terms = []
            
            # Insurance concept mappings
            if 'cash value' in concept:
                related_terms.extend(['growth', 'accumulation', 'surrender', 'loan', 'withdrawal'])
            elif 'premium' in concept:
                related_terms.extend(['payment', 'cost', 'affordability', 'funding'])
            elif 'death benefit' in concept:
                related_terms.extend(['coverage', 'protection', 'beneficiary', 'payout'])
            elif 'policy' in concept:
                related_terms.extend(['terms', 'conditions', 'features', 'benefits'])
            
            return related_terms
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error getting concept related terms: {e}")
            return []
    
    def _calculate_partial_relevance(self, content: str, source: str, topic: str) -> float:
        """Calculate partial relevance when exact match isn't found"""
        try:
            topic_words = topic.split()
            content_words = content.split()
            source_words = source.split()
            
            # Calculate word overlap
            topic_set = set(topic_words)
            content_set = set(content_words)
            source_set = set(source_words)
            
            # Check content overlap
            content_overlap = len(topic_set.intersection(content_set))
            content_total = len(topic_set.union(content_set))
            content_score = content_overlap / content_total if content_total > 0 else 0
            
            # Check source overlap
            source_overlap = len(topic_set.intersection(source_set))
            source_total = len(topic_set.union(source_set))
            source_score = source_overlap / source_total if source_total > 0 else 0
            
            # Return average of content and source scores
            return (content_score + source_score) / 2
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error calculating partial relevance: {e}")
            return 0.0
    
    def get_retrieval_stats(self, original_count: int, filtered_count: int, 
                           avg_context_score: float) -> Dict[str, Any]:
        """Get statistics about the context-aware retrieval process"""
        try:
            return {
                "original_document_count": original_count,
                "filtered_document_count": filtered_count,
                "filtering_ratio": filtered_count / original_count if original_count > 0 else 0,
                "average_context_relevance": avg_context_score,
                "context_relevance_threshold": self.context_relevance_threshold,
                "max_context_documents": self.max_context_documents
            }
        except Exception as e:
            logger.error(f"🔍 CONTEXT RETRIEVER: Error getting retrieval stats: {e}")
            return {}
