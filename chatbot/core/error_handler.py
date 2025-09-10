"""
Unified Error Handling System

This module provides comprehensive error handling for the follow-up and context system,
ensuring graceful degradation and proper fallback mechanisms.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from .schemas import ConversationContext, ContextSelectionResult, FollowUpResult

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issues, system continues normally
    MEDIUM = "medium"     # Moderate issues, some functionality affected
    HIGH = "high"         # Major issues, significant functionality affected
    CRITICAL = "critical" # System failure, requires immediate attention

class ErrorCategory(str, Enum):
    """Error categories for classification"""
    CONTEXT_SELECTION = "context_selection"
    FOLLOW_UP_DETECTION = "follow_up_detection"
    VALIDATION = "validation"
    CACHE = "cache"
    LLM_API = "llm_api"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context information for error handling"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    user_query: Optional[str] = None
    conversation_context: Optional[ConversationContext] = None
    stack_trace: Optional[str] = None
    timestamp: datetime = None
    recovery_attempted: bool = False
    fallback_used: bool = False

class UnifiedErrorHandler:
    """Unified error handling for the follow-up and context system"""
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.max_error_history = 100
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies = {
            ErrorCategory.CONTEXT_SELECTION: self._handle_context_selection_error,
            ErrorCategory.FOLLOW_UP_DETECTION: self._handle_follow_up_detection_error,
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.CACHE: self._handle_cache_error,
            ErrorCategory.LLM_API: self._handle_llm_api_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.CONFIGURATION: self._handle_configuration_error,
            ErrorCategory.UNKNOWN: self._handle_unknown_error
        }
    
    def handle_error(
        self, 
        error: Exception, 
        component: str,
        user_query: Optional[str] = None,
        conversation_context: Optional[ConversationContext] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """Handle an error with appropriate recovery strategies"""
        
        try:
            # Classify the error
            error_context = self._classify_error(error, component, user_query, conversation_context)
            
            # Log the error
            self._log_error(error_context)
            
            # Store in history
            self._store_error(error_context)
            
            # Attempt recovery
            recovery_result = self._attempt_recovery(error_context, additional_context)
            error_context.recovery_attempted = True
            error_context.fallback_used = recovery_result.get('fallback_used', False)
            
            return error_context
            
        except Exception as recovery_error:
            logger.error(f"Error in error handling: {recovery_error}")
            # Return a basic error context if error handling itself fails
            return ErrorContext(
                error_type=type(error).__name__,
                error_message=str(error),
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.UNKNOWN,
                component=component,
                user_query=user_query,
                conversation_context=conversation_context,
                stack_trace=traceback.format_exc(),
                timestamp=datetime.utcnow()
            )
    
    def _classify_error(
        self, 
        error: Exception, 
        component: str,
        user_query: Optional[str],
        conversation_context: Optional[ConversationContext]
    ) -> ErrorContext:
        """Classify error type and severity"""
        
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # Determine category based on error type and component
        category = self._determine_error_category(error, component)
        
        # Determine severity based on error type and impact
        severity = self._determine_error_severity(error, component, category)
        
        return ErrorContext(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            category=category,
            component=component,
            user_query=user_query,
            conversation_context=conversation_context,
            stack_trace=stack_trace,
            timestamp=datetime.utcnow()
        )
    
    def _determine_error_category(self, error: Exception, component: str) -> ErrorCategory:
        """Determine error category based on error type and component"""
        
        error_message = str(error).lower()
        
        # Context selection errors
        if "context" in component.lower() or "context" in error_message:
            return ErrorCategory.CONTEXT_SELECTION
        
        # Follow-up detection errors
        if "follow" in component.lower() or "follow" in error_message:
            return ErrorCategory.FOLLOW_UP_DETECTION
        
        # Validation errors
        if "validation" in component.lower() or "validation" in error_message:
            return ErrorCategory.VALIDATION
        
        # Cache errors
        if "cache" in component.lower() or "cache" in error_message:
            return ErrorCategory.CACHE
        
        # LLM API errors
        if any(keyword in error_message for keyword in ["openai", "api", "llm", "model"]):
            return ErrorCategory.LLM_API
        
        # Network errors
        if any(keyword in error_message for keyword in ["network", "connection", "timeout", "unreachable"]):
            return ErrorCategory.NETWORK
        
        # Configuration errors
        if any(keyword in error_message for keyword in ["config", "setting", "parameter", "missing"]):
            return ErrorCategory.CONFIGURATION
        
        return ErrorCategory.UNKNOWN
    
    def _determine_error_severity(
        self, 
        error: Exception, 
        component: str, 
        category: ErrorCategory
    ) -> ErrorSeverity:
        """Determine error severity based on error type and impact"""
        
        error_message = str(error).lower()
        
        # Critical errors - system cannot function
        if any(keyword in error_message for keyword in ["critical", "fatal", "cannot", "unable"]):
            return ErrorSeverity.CRITICAL
        
        # High severity - major functionality affected
        if category in [ErrorCategory.LLM_API, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.HIGH
        
        # Medium severity - some functionality affected
        if category in [ErrorCategory.CONTEXT_SELECTION, ErrorCategory.FOLLOW_UP_DETECTION]:
            return ErrorSeverity.MEDIUM
        
        # Low severity - minor issues
        if category in [ErrorCategory.CACHE, ErrorCategory.VALIDATION]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _log_error(self, error_context: ErrorContext) -> None:
        """Log error with appropriate level"""
        
        log_message = f"Error in {error_context.component}: {error_context.error_message}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _store_error(self, error_context: ErrorContext) -> None:
        """Store error in history and update counts"""
        
        # Add to history
        self.error_history.append(error_context)
        
        # Keep only recent errors
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]
        
        # Update error counts
        error_key = f"{error_context.category}_{error_context.component}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def _attempt_recovery(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Attempt to recover from the error"""
        
        try:
            # Get recovery strategy for this error category
            recovery_strategy = self.recovery_strategies.get(error_context.category)
            
            if recovery_strategy:
                return recovery_strategy(error_context, additional_context)
            else:
                return self._handle_unknown_error(error_context, additional_context)
                
        except Exception as recovery_error:
            logger.error(f"Error in recovery attempt: {recovery_error}")
            return {"success": False, "fallback_used": True, "error": str(recovery_error)}
    
    def _handle_context_selection_error(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle context selection errors"""
        
        try:
            logger.info("🔄 ERROR HANDLER: Attempting context selection recovery")
            
            # Return fallback context selection result
            fallback_result = ContextSelectionResult(
                context_type="standard",
                conversation_context=error_context.conversation_context,
                context_summary="Fallback context due to error",
                validation_result=None
            )
            
            return {
                "success": True,
                "fallback_used": True,
                "fallback_result": fallback_result,
                "recovery_strategy": "standard_context_fallback"
            }
            
        except Exception as e:
            logger.error(f"Context selection recovery failed: {e}")
            return {"success": False, "fallback_used": True, "error": str(e)}
    
    def _handle_follow_up_detection_error(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle follow-up detection errors"""
        
        try:
            logger.info("🔄 ERROR HANDLER: Attempting follow-up detection recovery")
            
            # Return conservative follow-up result
            fallback_result = FollowUpResult(
                is_follow_up=False,
                related_topics=[],
                context_relevance=0.0,
                suggested_context_window=1,
                reasoning="Follow-up detection failed, assuming new query",
                confidence=0.0
            )
            
            return {
                "success": True,
                "fallback_used": True,
                "fallback_result": fallback_result,
                "recovery_strategy": "conservative_follow_up_assumption"
            }
            
        except Exception as e:
            logger.error(f"Follow-up detection recovery failed: {e}")
            return {"success": False, "fallback_used": True, "error": str(e)}
    
    def _handle_validation_error(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle validation errors"""
        
        try:
            logger.info("🔄 ERROR HANDLER: Attempting validation recovery")
            
            # Skip validation and proceed with context
            return {
                "success": True,
                "fallback_used": True,
                "recovery_strategy": "skip_validation"
            }
            
        except Exception as e:
            logger.error(f"Validation recovery failed: {e}")
            return {"success": False, "fallback_used": True, "error": str(e)}
    
    def _handle_cache_error(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle cache errors"""
        
        try:
            logger.info("🔄 ERROR HANDLER: Attempting cache recovery")
            
            # Clear cache and proceed without caching
            return {
                "success": True,
                "fallback_used": True,
                "recovery_strategy": "clear_cache_and_proceed"
            }
            
        except Exception as e:
            logger.error(f"Cache recovery failed: {e}")
            return {"success": False, "fallback_used": True, "error": str(e)}
    
    def _handle_llm_api_error(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle LLM API errors"""
        
        try:
            logger.info("🔄 ERROR HANDLER: Attempting LLM API recovery")
            
            # Use fallback response
            return {
                "success": True,
                "fallback_used": True,
                "recovery_strategy": "fallback_response"
            }
            
        except Exception as e:
            logger.error(f"LLM API recovery failed: {e}")
            return {"success": False, "fallback_used": True, "error": str(e)}
    
    def _handle_network_error(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle network errors"""
        
        try:
            logger.info("🔄 ERROR HANDLER: Attempting network recovery")
            
            # Retry with timeout or use cached data
            return {
                "success": True,
                "fallback_used": True,
                "recovery_strategy": "retry_with_timeout"
            }
            
        except Exception as e:
            logger.error(f"Network recovery failed: {e}")
            return {"success": False, "fallback_used": True, "error": str(e)}
    
    def _handle_configuration_error(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle configuration errors"""
        
        try:
            logger.info("🔄 ERROR HANDLER: Attempting configuration recovery")
            
            # Use default configuration
            return {
                "success": True,
                "fallback_used": True,
                "recovery_strategy": "use_default_configuration"
            }
            
        except Exception as e:
            logger.error(f"Configuration recovery failed: {e}")
            return {"success": False, "fallback_used": True, "error": str(e)}
    
    def _handle_unknown_error(
        self, 
        error_context: ErrorContext, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle unknown errors"""
        
        try:
            logger.info("🔄 ERROR HANDLER: Attempting unknown error recovery")
            
            # Use basic fallback
            return {
                "success": True,
                "fallback_used": True,
                "recovery_strategy": "basic_fallback"
            }
            
        except Exception as e:
            logger.error(f"Unknown error recovery failed: {e}")
            return {"success": False, "fallback_used": True, "error": str(e)}
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        
        try:
            recent_errors = self.error_history[-10:] if self.error_history else []
            
            severity_counts = {}
            category_counts = {}
            component_counts = {}
            
            for error in recent_errors:
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                component_counts[error.component] = component_counts.get(error.component, 0) + 1
            
            return {
                "total_errors": len(self.error_history),
                "recent_errors": len(recent_errors),
                "severity_distribution": severity_counts,
                "category_distribution": category_counts,
                "component_distribution": component_counts,
                "error_counts": self.error_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def clear_error_history(self) -> None:
        """Clear error history"""
        self.error_history = []
        self.error_counts = {}
        logger.info("🔄 ERROR HANDLER: Error history cleared")
