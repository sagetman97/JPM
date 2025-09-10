"""
Context Validation System

This module provides context validation, quality scoring, and metrics tracking
for the unified follow-up and context system.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from .schemas import ContextValidationResult, ContextMetrics, FollowUpResult, ConversationContext

logger = logging.getLogger(__name__)

class ContextValidator:
    """Validates context selection quality and relevance"""
    
    def __init__(self):
        self.metrics = ContextMetrics()
        self.validation_history: List[Dict[str, Any]] = []
        self.min_relevance_threshold = 0.3
        self.min_quality_threshold = 0.4
        self.min_confidence_threshold = 0.5
        
    async def validate_context_selection(
        self, 
        query: str, 
        selected_context: Optional[Dict[str, Any]], 
        follow_up_result: Optional[FollowUpResult],
        conversation_context: ConversationContext
    ) -> ContextValidationResult:
        """Validate the quality and relevance of selected context"""
        
        try:
            logger.info("🔍 CONTEXT VALIDATOR: Starting context validation")
            
            # Initialize validation result
            issues = []
            recommendations = []
            
            # Check if context was selected
            if not selected_context:
                return ContextValidationResult(
                    is_valid=False,
                    relevance_score=0.0,
                    quality_score=0.0,
                    confidence=0.0,
                    issues=["No context selected"],
                    recommendations=["Use fallback context or generate new response"],
                    fallback_available=True
                )
            
            # Validate context relevance
            relevance_score = await self._calculate_relevance_score(
                query, selected_context, follow_up_result
            )
            
            # Validate context quality
            quality_score = await self._calculate_quality_score(
                selected_context, conversation_context
            )
            
            # Calculate overall confidence
            confidence = (relevance_score + quality_score) / 2
            
            # Check for specific issues
            if relevance_score < self.min_relevance_threshold:
                issues.append(f"Low relevance score: {relevance_score:.2f}")
                recommendations.append("Consider using more recent context or fallback")
            
            if quality_score < self.min_quality_threshold:
                issues.append(f"Low quality score: {quality_score:.2f}")
                recommendations.append("Context may be incomplete or outdated")
            
            if confidence < self.min_confidence_threshold:
                issues.append(f"Low confidence: {confidence:.2f}")
                recommendations.append("Consider using fallback context")
            
            # Check for context staleness
            if self._is_context_stale(selected_context):
                issues.append("Context is stale (older than 10 minutes)")
                recommendations.append("Use more recent context")
            
            # Check for context completeness
            if not self._is_context_complete(selected_context):
                issues.append("Context appears incomplete")
                recommendations.append("Verify context contains necessary information")
            
            # Determine if context is valid
            is_valid = (
                relevance_score >= self.min_relevance_threshold and
                quality_score >= self.min_quality_threshold and
                confidence >= self.min_confidence_threshold and
                not self._is_context_stale(selected_context)
            )
            
            # Update metrics
            self._update_metrics(relevance_score, quality_score, confidence, is_valid)
            
            # Log validation result
            logger.info(f"🔍 CONTEXT VALIDATOR: Validation complete - Valid: {is_valid}, Relevance: {relevance_score:.2f}, Quality: {quality_score:.2f}")
            
            return ContextValidationResult(
                is_valid=is_valid,
                relevance_score=relevance_score,
                quality_score=quality_score,
                confidence=confidence,
                issues=issues,
                recommendations=recommendations,
                fallback_available=True
            )
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT VALIDATOR: Error in context validation: {e}")
            return ContextValidationResult(
                is_valid=False,
                relevance_score=0.0,
                quality_score=0.0,
                confidence=0.0,
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Use fallback context"],
                fallback_available=True
            )
    
    async def _calculate_relevance_score(
        self, 
        query: str, 
        selected_context: Dict[str, Any], 
        follow_up_result: Optional[FollowUpResult]
    ) -> float:
        """Calculate how relevant the selected context is to the query"""
        
        try:
            score = 0.0
            
            # Base relevance from follow-up detection
            if follow_up_result:
                score += follow_up_result.context_relevance * 0.4
            
            # Content relevance scoring
            content = selected_context.get('content', '') or selected_context.get('assistant_response', '')
            query_lower = query.lower()
            content_lower = content.lower()
            
            # Check for keyword overlap
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            word_overlap = len(query_words.intersection(content_words))
            word_relevance = min(word_overlap / max(len(query_words), 1), 1.0)
            score += word_relevance * 0.3
            
            # Check for structured data relevance
            if self._contains_structured_data(content):
                if any(keyword in query_lower for keyword in ['report', 'analysis', 'data', 'results', 'summary']):
                    score += 0.2
            
            # Check for topic relevance
            if follow_up_result and follow_up_result.related_topics:
                topic_matches = sum(1 for topic in follow_up_result.related_topics if topic.lower() in content_lower)
                topic_relevance = topic_matches / len(follow_up_result.related_topics)
                score += topic_relevance * 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT VALIDATOR: Error calculating relevance score: {e}")
            return 0.0
    
    async def _calculate_quality_score(
        self, 
        selected_context: Dict[str, Any], 
        conversation_context: ConversationContext
    ) -> float:
        """Calculate the quality of the selected context"""
        
        try:
            score = 0.0
            
            # Check content completeness
            content = selected_context.get('content', '') or selected_context.get('assistant_response', '')
            if len(content) > 50:  # Minimum content length
                score += 0.2
            
            # Check for structured data
            if self._contains_structured_data(content):
                score += 0.3
            
            # Check for recent context
            timestamp = selected_context.get('timestamp')
            if timestamp:
                age_hours = (time.time() - timestamp) / 3600
                if age_hours < 1:  # Less than 1 hour old
                    score += 0.2
                elif age_hours < 24:  # Less than 1 day old
                    score += 0.1
            
            # Check for user query presence
            if selected_context.get('user_query'):
                score += 0.1
            
            # Check for assistant response presence
            if selected_context.get('assistant_response'):
                score += 0.1
            
            # Check for metadata completeness
            if selected_context.get('metadata'):
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT VALIDATOR: Error calculating quality score: {e}")
            return 0.0
    
    def _is_context_stale(self, selected_context: Dict[str, Any]) -> bool:
        """Check if context is too old"""
        try:
            timestamp = selected_context.get('timestamp')
            if not timestamp:
                return True  # No timestamp means stale
            
            age_minutes = (time.time() - timestamp) / 60
            return age_minutes > 10  # Stale if older than 10 minutes
            
        except Exception:
            return True
    
    def _is_context_complete(self, selected_context: Dict[str, Any]) -> bool:
        """Check if context has necessary information"""
        try:
            # Check for essential fields
            has_content = bool(selected_context.get('content') or selected_context.get('assistant_response'))
            has_user_query = bool(selected_context.get('user_query'))
            
            return has_content and has_user_query
            
        except Exception:
            return False
    
    def _contains_structured_data(self, content: str) -> bool:
        """Check if content contains structured data indicators"""
        indicators = [
            "total assets:", "risk level:", "life insurance need:",
            "portfolio analysis completed", "report available:",
            "download portfolio_report.pdf", "portfolio health score:",
            "asset allocation:", "recommended coverage:",
            "product recommendation:", "financial summary:",
            "calculation completed", "analysis results:",
            "coverage gap:", "monthly contribution:"
        ]
        return any(indicator.lower() in content.lower() for indicator in indicators)
    
    def _update_metrics(
        self, 
        relevance_score: float, 
        quality_score: float, 
        confidence: float, 
        is_valid: bool
    ) -> None:
        """Update context selection metrics"""
        
        try:
            self.metrics.total_selections += 1
            
            # Update running averages
            if self.metrics.total_selections == 1:
                self.metrics.average_relevance = relevance_score
                self.metrics.average_quality = quality_score
            else:
                # Calculate running average
                self.metrics.average_relevance = (
                    (self.metrics.average_relevance * (self.metrics.total_selections - 1) + relevance_score) 
                    / self.metrics.total_selections
                )
                self.metrics.average_quality = (
                    (self.metrics.average_quality * (self.metrics.total_selections - 1) + quality_score) 
                    / self.metrics.total_selections
                )
            
            # Update accuracy (valid selections / total selections)
            if is_valid:
                self.metrics.selection_accuracy = (
                    (self.metrics.selection_accuracy * (self.metrics.total_selections - 1) + 1.0) 
                    / self.metrics.total_selections
                )
            else:
                self.metrics.selection_accuracy = (
                    (self.metrics.selection_accuracy * (self.metrics.total_selections - 1) + 0.0) 
                    / self.metrics.total_selections
                )
            
            # Track validation failures
            if not is_valid:
                self.metrics.validation_failures += 1
            
            # Store validation history
            self.validation_history.append({
                'timestamp': time.time(),
                'relevance_score': relevance_score,
                'quality_score': quality_score,
                'confidence': confidence,
                'is_valid': is_valid
            })
            
            # Keep only last 100 validations
            if len(self.validation_history) > 100:
                self.validation_history = self.validation_history[-100:]
                
        except Exception as e:
            logger.error(f"🔍 CONTEXT VALIDATOR: Error updating metrics: {e}")
    
    def get_metrics(self) -> ContextMetrics:
        """Get current context selection metrics"""
        return self.metrics
    
    def get_validation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent validation history"""
        return self.validation_history[-limit:] if self.validation_history else []
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = ContextMetrics()
        self.validation_history = []
        logger.info("🔍 CONTEXT VALIDATOR: Metrics reset")
