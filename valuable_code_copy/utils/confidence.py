"""
Confidence scoring utilities for the Financial Advisor Assistant.
Based on patterns from AIE7 course materials.
"""

import re
from typing import Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from config.settings import settings


def assess_confidence_score(response: str, query: str, retrieved_docs: list) -> float:
    """
    Assess confidence score for a RAG response.
    Based on multiple factors including response quality and retrieval relevance.
    
    Args:
        response: The generated response
        query: The original user query
        retrieved_docs: List of retrieved documents
        
    Returns:
        Confidence score between 0 and 1
    """
    scores = []
    
    # Factor 1: Response completeness
    completeness_score = _assess_completeness(response, query)
    scores.append(completeness_score)
    
    # Factor 2: Response specificity
    specificity_score = _assess_specificity(response, query)
    scores.append(specificity_score)
    
    # Factor 3: Retrieval relevance
    relevance_score = _assess_retrieval_relevance(query, retrieved_docs)
    scores.append(relevance_score)
    
    # Factor 4: Response coherence
    coherence_score = _assess_coherence(response)
    scores.append(coherence_score)
    
    # Factor 5: Financial accuracy indicators
    accuracy_score = _assess_financial_accuracy(response)
    scores.append(accuracy_score)
    
    # Weighted average of all scores
    weights = [0.25, 0.25, 0.2, 0.15, 0.15]
    confidence_score = sum(score * weight for score, weight in zip(scores, weights))
    
    return min(max(confidence_score, 0.0), 1.0)


def _assess_completeness(response: str, query: str) -> float:
    """
    Assess how completely the response addresses the query.
    """
    # Check for key financial terms that should be present
    financial_terms = [
        "life insurance", "coverage", "premium", "death benefit",
        "term", "whole life", "universal", "policy", "beneficiary",
        "tax", "investment", "portfolio", "risk", "diversification"
    ]
    
    query_lower = query.lower()
    response_lower = response.lower()
    
    # Count relevant terms in response
    relevant_terms = [term for term in financial_terms if term in query_lower]
    if not relevant_terms:
        return 0.8  # Default score if no specific terms
    
    found_terms = sum(1 for term in relevant_terms if term in response_lower)
    return min(found_terms / len(relevant_terms), 1.0)


def _assess_specificity(response: str, query: str) -> float:
    """
    Assess how specific and actionable the response is.
    """
    # Indicators of specificity
    specificity_indicators = [
        r'\$\d+',  # Dollar amounts
        r'\d+%',   # Percentages
        r'\d+\s*years?',  # Time periods
        r'coverage\s+amount',  # Specific coverage mentions
        r'recommend',  # Recommendations
        r'consider',   # Considerations
        r'typically',  # General guidelines
        r'usually'     # General guidelines
    ]
    
    response_lower = response.lower()
    specificity_count = sum(1 for pattern in specificity_indicators 
                          if re.search(pattern, response_lower))
    
    # Normalize to 0-1 scale
    return min(specificity_count / 3, 1.0)


def _assess_retrieval_relevance(query: str, retrieved_docs: list) -> float:
    """
    Assess relevance of retrieved documents to the query.
    """
    if not retrieved_docs:
        return 0.0
    
    query_terms = set(query.lower().split())
    total_relevance = 0.0
    
    for doc in retrieved_docs:
        doc_content = doc.page_content.lower()
        doc_terms = set(doc_content.split())
        
        # Calculate overlap
        overlap = len(query_terms.intersection(doc_terms))
        relevance = overlap / len(query_terms) if query_terms else 0.0
        total_relevance += relevance
    
    return min(total_relevance / len(retrieved_docs), 1.0)


def _assess_coherence(response: str) -> float:
    """
    Assess the coherence and readability of the response.
    """
    # Check for sentence structure
    sentences = re.split(r'[.!?]+', response)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return 0.0
    
    # Check for proper sentence length
    avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
    
    # Ideal sentence length is 15-25 words
    if 15 <= avg_sentence_length <= 25:
        length_score = 1.0
    elif 10 <= avg_sentence_length <= 30:
        length_score = 0.8
    else:
        length_score = 0.5
    
    # Check for financial terminology consistency
    financial_terms = [
        "life insurance", "policy", "coverage", "premium",
        "death benefit", "cash value", "term", "whole life"
    ]
    
    term_consistency = sum(1 for term in financial_terms 
                          if term in response.lower()) / len(financial_terms)
    
    return (length_score + term_consistency) / 2


def _assess_financial_accuracy(response: str) -> float:
    """
    Assess indicators of financial accuracy in the response.
    """
    # Positive indicators
    positive_indicators = [
        "consult with a financial advisor",
        "speak with a licensed professional",
        "consider your specific situation",
        "individual circumstances",
        "professional advice",
        "regulatory requirements",
        "compliance",
        "disclaimer"
    ]
    
    # Negative indicators
    negative_indicators = [
        "guaranteed returns",
        "risk-free",
        "always",
        "never",
        "definitely",
        "certainly"
    ]
    
    response_lower = response.lower()
    
    positive_count = sum(1 for indicator in positive_indicators 
                        if indicator in response_lower)
    negative_count = sum(1 for indicator in negative_indicators 
                        if indicator in response_lower)
    
    # Calculate score
    positive_score = min(positive_count / 3, 1.0)
    negative_penalty = min(negative_count * 0.2, 0.5)
    
    return max(positive_score - negative_penalty, 0.0)


def should_use_external_search(confidence_score: float) -> bool:
    """
    Determine if external search should be used based on confidence score.
    
    Args:
        confidence_score: Confidence score between 0 and 1
        
    Returns:
        True if external search should be used
    """
    return confidence_score < settings.CONFIDENCE_THRESHOLD


def get_confidence_feedback(confidence_score: float) -> str:
    """
    Get human-readable feedback about confidence level.
    
    Args:
        confidence_score: Confidence score between 0 and 1
        
    Returns:
        Feedback message
    """
    if confidence_score >= 0.8:
        return "High confidence response based on our knowledge base."
    elif confidence_score >= 0.6:
        return "Moderate confidence. Consider verifying with additional sources."
    elif confidence_score >= 0.4:
        return "Low confidence. Searching for additional information..."
    else:
        return "Very low confidence. Using external search to improve response." 