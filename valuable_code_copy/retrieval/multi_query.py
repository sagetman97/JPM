"""
Multi-Query Retrieval Implementation

Generates multiple queries from a single query to improve retrieval coverage.
Based on patterns from AIE7 Advanced Retrieval course materials.
"""

from typing import List, Dict, Any, Optional
from langchain.retrievers import MultiQueryRetriever
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

from config.settings import settings

class EnhancedMultiQueryRetriever(BaseRetriever):
    """
    Enhanced multi-query retriever with custom query generation.
    
    This implementation follows the pattern from AIE7 Advanced Retrieval course,
    generating multiple queries to improve retrieval coverage.
    """
    
    def __init__(
        self,
        base_retriever: BaseRetriever,
        llm: ChatOpenAI,
        query_count: int = 3,
        max_worker_threads: int = 4
    ):
        """
        Initialize enhanced multi-query retriever.
        
        Args:
            base_retriever: Base retriever to use for document retrieval
            llm: Language model for query generation
            query_count: Number of queries to generate
            max_worker_threads: Maximum number of worker threads
        """
        self.base_retriever = base_retriever
        self.llm = llm
        self.query_count = query_count
        self.max_worker_threads = max_worker_threads
        
        # Create query generation prompt
        self.query_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at generating diverse search queries for life insurance and financial planning topics.

Your task is to generate {query_count} different search queries that would help find relevant information for the user's question.

**Guidelines:**
- Generate queries that explore different aspects of the topic
- Include both broad and specific queries
- Use different terminology and synonyms
- Consider different user perspectives (advisor, client, researcher)
- Focus on life insurance, financial planning, and portfolio management

**Query Types to Generate:**
1. **Conceptual**: Basic definitions and explanations
2. **Practical**: How-to and implementation questions
3. **Comparative**: Comparison between different options
4. **Technical**: Specific details and calculations
5. **Contextual**: How it fits into broader financial planning

**Example Transformations:**
- "What is whole life insurance?" → ["whole life insurance definition", "permanent life insurance benefits", "cash value life insurance explanation"]
- "How much coverage do I need?" → ["life insurance needs calculation", "coverage amount determination", "human life value method"]

Generate {query_count} diverse queries that would help find comprehensive information about the topic.
"""),
            ("user", "Original query: {query}"),
        ])
        
        # Create the query generation chain
        self.query_generator = self.query_prompt | self.llm | JsonOutputParser()
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Retrieve documents using multi-query approach.
        
        Args:
            query: Original search query
            run: Callback manager
            
        Returns:
            List of relevant documents
        """
        # Generate multiple queries
        try:
            generated_queries = self._generate_queries(query)
        except Exception as e:
            # Fallback to original query if generation fails
            generated_queries = [query]
        
        # Retrieve documents for each query
        all_documents = []
        for generated_query in generated_queries:
            try:
                docs = self.base_retriever.get_relevant_documents(generated_query)
                all_documents.extend(docs)
            except Exception as e:
                print(f"Error retrieving documents for query '{generated_query}': {e}")
                continue
        
        # Remove duplicates and return top results
        unique_docs = self._remove_duplicates(all_documents)
        return unique_docs[:self.base_retriever.search_kwargs.get("k", 4)]
    
    def _generate_queries(self, original_query: str) -> List[str]:
        """
        Generate multiple queries from the original query.
        
        Args:
            original_query: Original user query
            
        Returns:
            List of generated queries
        """
        try:
            # Generate queries using LLM
            result = self.query_generator.invoke({
                "query": original_query,
                "query_count": self.query_count
            })
            
            # Extract queries from result
            if isinstance(result, dict) and "queries" in result:
                queries = result["queries"]
            elif isinstance(result, list):
                queries = result
            else:
                # Fallback: create simple variations
                queries = self._create_simple_variations(original_query)
            
            # Ensure we have the right number of queries
            if len(queries) < self.query_count:
                additional_queries = self._create_simple_variations(original_query)
                queries.extend(additional_queries[:self.query_count - len(queries)])
            
            return queries[:self.query_count]
            
        except Exception as e:
            print(f"Error generating queries: {e}")
            return self._create_simple_variations(original_query)
    
    def _create_simple_variations(self, query: str) -> List[str]:
        """
        Create simple query variations as fallback.
        
        Args:
            query: Original query
            
        Returns:
            List of query variations
        """
        variations = [query]
        
        # Add common variations
        if "life insurance" in query.lower():
            variations.extend([
                query.replace("life insurance", "life coverage"),
                query.replace("life insurance", "life policy"),
                query + " benefits",
                query + " costs"
            ])
        
        if "calculate" in query.lower() or "how much" in query.lower():
            variations.extend([
                query.replace("calculate", "determine"),
                query.replace("how much", "what amount"),
                "life insurance needs analysis",
                "coverage amount calculation"
            ])
        
        if "portfolio" in query.lower():
            variations.extend([
                query.replace("portfolio", "investment"),
                query.replace("portfolio", "financial plan"),
                "life insurance asset allocation",
                "insurance portfolio integration"
            ])
        
        return variations[:self.query_count]
    
    def _remove_duplicates(self, documents: List[Document]) -> List[Document]:
        """
        Remove duplicate documents based on content.
        
        Args:
            documents: List of documents
            
        Returns:
            List of unique documents
        """
        seen_content = set()
        unique_docs = []
        
        for doc in documents:
            content_hash = hash(doc.page_content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_docs.append(doc)
        
        return unique_docs
    
    def get_query_analysis(self, query: str) -> Dict[str, Any]:
        """
        Get analysis of query generation and retrieval.
        
        Args:
            query: Original query
            
        Returns:
            Query analysis statistics
        """
        try:
            generated_queries = self._generate_queries(query)
            
            # Get documents for each query
            query_results = {}
            total_docs = 0
            
            for i, gen_query in enumerate(generated_queries):
                try:
                    docs = self.base_retriever.get_relevant_documents(gen_query)
                    query_results[f"query_{i+1}"] = {
                        "query": gen_query,
                        "doc_count": len(docs),
                        "documents": [doc.page_content[:100] + "..." for doc in docs]
                    }
                    total_docs += len(docs)
                except Exception as e:
                    query_results[f"query_{i+1}"] = {
                        "query": gen_query,
                        "error": str(e)
                    }
            
            return {
                "original_query": query,
                "generated_queries": generated_queries,
                "query_results": query_results,
                "total_documents_found": total_docs,
                "average_docs_per_query": total_docs / len(generated_queries) if generated_queries else 0
            }
            
        except Exception as e:
            return {
                "original_query": query,
                "error": str(e)
            } 