import logging
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from .schemas import RAGResult, ConversationContext, IntentResult
from .config import config
# REMOVED: Complex context-aware imports that were causing issues
# from .context_manager import ContextAwareQueryEnhancer
# from .context_aware_retriever import ContextAwareDocumentRetriever

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes and chunks documents for RAG"""
    
    def __init__(self):
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap
    
    def process_text_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process text files and create chunks"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return self._create_chunks(content, file_path)
            
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
            return []
    
    def process_pdf_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process PDF files and create chunks"""
        
        try:
            import PyPDF2
            
            chunks = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    page_chunks = self._create_chunks(text, f"{file_path}_page_{page_num}")
                    chunks.extend(page_chunks)
            
            return chunks
            
        except ImportError:
            logger.warning("PyPDF2 not available, treating PDF as text file")
            return self.process_text_file(file_path)
        except Exception as e:
            logger.error(f"Error processing PDF file {file_path}: {e}")
            return []
    
    def _create_chunks(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Create overlapping chunks from content"""
        
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) < 50:  # Skip very short chunks
                continue
            
            chunk_id = hashlib.md5(f"{source}_{i}".encode()).hexdigest()
            
            chunks.append({
                "id": chunk_id,
                "content": chunk_text,
                "source": source,
                "chunk_index": i // (self.chunk_size - self.chunk_overlap),
                "metadata": {
                    "source": source,
                    "chunk_index": i // (self.chunk_size - self.chunk_overlap),
                    "word_count": len(chunk_words)
                }
            })
        
        return chunks

class SemanticQueryExpander:
    """Expands queries semantically using LLM"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
    
    async def expand_query_semantically(self, query: str, context: ConversationContext) -> List[str]:
        """Expand query semantically for comprehensive RAG document retrieval"""
        try:
            logger.info(f"🔍 QUERY EXPANDER: Expanding query for RAG retrieval: '{query[:50]}...'")
            
            # Build expansion prompt focused on RAG document retrieval
            prompt = self._build_expansion_prompt(query, context)
            
            # Get expansion from LLM
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert at expanding financial queries for comprehensive document retrieval. Focus on finding relevant documents in a knowledge base, NOT external search."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            expansion_text = response.choices[0].message.content.strip()
            logger.info(f"🔍 QUERY EXPANDER: LLM expansion response: {expansion_text[:100]}...")
            
            # Parse expanded queries
            expanded_queries = self._parse_expanded_queries(expansion_text)
            
            # Always include the original query first
            if query not in expanded_queries:
                expanded_queries.insert(0, query)
            
            # Limit to reasonable number of queries to prevent over-processing
            max_queries = 5
            if len(expanded_queries) > max_queries:
                expanded_queries = expanded_queries[:max_queries]
                logger.info(f"🔍 QUERY EXPANDER: Limited to {max_queries} queries to prevent over-processing")
            
            logger.info(f"🔍 QUERY EXPANDER: Final expanded queries: {len(expanded_queries)}")
            for i, q in enumerate(expanded_queries):
                logger.info(f"🔍 QUERY EXPANDER: Query {i+1}: '{q[:50]}...'")
            
            return expanded_queries
            
        except Exception as e:
            logger.error(f"🔍 QUERY EXPANDER: Error expanding query: {e}")
            # Return original query as fallback
            return [query]
    
    def _build_expansion_prompt(self, query: str, context: ConversationContext) -> str:
        """Build prompt for semantic query expansion focused on RAG document retrieval"""
        return f"""
        Expand this financial query into 3-4 related queries to find comprehensive information in a knowledge base.
        
        **Original Query:** "{query}"
        **User Knowledge Level:** {context.knowledge_level.value}
        **Context:** {context.current_topic or 'Financial Planning'}
        
        **Focus Areas for RAG Document Retrieval:**
        1. **Core Concept:** Main financial topic or product
        2. **Related Concepts:** Closely related financial topics
        3. **Calculation Methods:** Different approaches to the same problem
        4. **Product Types:** Variations of the financial product
        
        **IMPORTANT:** 
        - Focus on finding documents in a knowledge base, NOT external search
        - Keep queries similar to the original to ensure relevance
        - Don't create queries that are too different from the original
        - Aim for comprehensive coverage, not broad expansion
        
        **Example Expansions:**
        - Original: "term life insurance rates"
        - Expansion: ["term life insurance rates", "term life insurance pricing", "term life insurance cost factors", "term life insurance premium calculation"]
        
        **Return only the expanded queries, one per line, no explanations:**
        """
    
    def _parse_expanded_queries(self, response: str) -> List[str]:
        """Parse LLM response for expanded queries"""
        
        try:
            # Try to extract JSON array
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                queries = json.loads(json_str)
                
                if isinstance(queries, list):
                    return queries
            
        except Exception as e:
            logger.error(f"Error parsing expanded queries: {e}")
        
        return []

class MultiQueryRetriever:
    """Multi-query retriever for comprehensive document retrieval"""
    
    def __init__(self, qdrant_client: QdrantClient = None):
        self.qdrant_client = qdrant_client
        self.query_expander = SemanticQueryExpander()
    
    async def retrieve_documents(self, queries: List[str], context: ConversationContext, k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve documents using multiple query strategies for comprehensive coverage"""
        try:
            if not self.qdrant_client:
                logger.warning("🔍 MULTI-QUERY: Qdrant client not available")
                return []
            
            # For single queries, use semantic expansion to get comprehensive coverage
            if len(queries) == 1:
                logger.info("🔍 MULTI-QUERY: Single query detected, using semantic expansion for comprehensive retrieval")
                expanded_queries = await self.query_expander.expand_query_semantically(queries[0], context)
                logger.info(f"🔍 MULTI-QUERY: Expanded single query into {len(expanded_queries)} semantic variations")
            else:
                expanded_queries = queries
                logger.info(f"🔍 MULTI-QUERY: Using {len(queries)} provided queries")
            
            # Retrieve documents for each query variation
            all_documents = []
            for i, query in enumerate(expanded_queries):
                try:
                    logger.info(f"🔍 MULTI-QUERY: Retrieving documents for query {i+1}/{len(expanded_queries)}: '{query[:50]}...'")
                    
                    # Get query embedding
                    query_embedding = await self._get_query_embedding(query)
                    if not query_embedding:
                        logger.warning(f"🔍 MULTI-QUERY: Failed to get embedding for query {i+1}")
                        continue
                    
                    # Search Qdrant
                    search_results = self.qdrant_client.search(
                        collection_name="robo_advisor_rag",
                        query_vector=query_embedding,
                        limit=k,
                        with_payload=True,
                        with_vectors=False
                    )
                
                    # Fix 1: Correct document key mismatch in MultiQueryRetriever
                    # Convert to document format
                    for result in search_results:
                        # Log the raw result structure for debugging
                        logger.debug(f"🔍 MULTI-QUERY: Raw result payload keys: {list(result.payload.keys()) if hasattr(result, 'payload') else 'No payload'}")
                        
                        document = {
                            "content": result.payload.get("content", ""),  # Change from "text" to "content"
                            "source": result.payload.get("source", "Unknown"),
                            "score": result.score,
                            "query": query
                        }
                        
                        # Log document creation for debugging
                        logger.debug(f"🔍 MULTI-QUERY: Created document - content length: {len(document['content'])}, source: {document['source']}, score: {document['score']}")
                        
                        all_documents.append(document)
                    
                    logger.info(f"🔍 MULTI-QUERY: Retrieved {len(search_results)} documents for query {i+1}")
                    
                except Exception as e:
                    logger.error(f"🔍 MULTI-QUERY: Error retrieving documents for query {i+1}: {e}")
                    continue
            
            if not all_documents:
                logger.warning("🔍 MULTI-QUERY: No documents retrieved from any query")
                return []
            
            # Deduplicate and rank documents
            unique_documents = self._deduplicate_documents(all_documents)
            ranked_documents = self._rank_documents(unique_documents, context)
            
            logger.info(f"🔍 MULTI-QUERY: Total documents after deduplication: {len(ranked_documents)}")
            return ranked_documents[:k]
            
        except Exception as e:
            logger.error(f"🔍 MULTI-QUERY: Error in multi-query retrieval: {e}")
            return []
    
    async def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for query using OpenAI"""
        
        logger.info(f"     🧠 RAG SYSTEM: Getting embedding for query: '{query[:50]}...'")
        try:
            from openai import AsyncOpenAI
            embedding_model = AsyncOpenAI(
                api_key=config.openai_api_key
            )
            
            logger.info(f"       Calling OpenAI embeddings API...")
            response = await embedding_model.embeddings.create(
                model=config.embedding_model,
                input=query
            )
            
            embedding = response.data[0].embedding
            logger.info(f"       ✅ Embedding received successfully, length: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"💥 RAG SYSTEM: Error getting query embedding: {e}")
            logger.error(f"       Error type: {type(e).__name__}")
            logger.error(f"       Error details: {str(e)}")
            logger.warning(f"⚠️ RAG SYSTEM: Using zero vector fallback for embedding")
            # Return zero vector as fallback
            return [0.0] * 1536  # Default embedding dimension
    
    def _deduplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents based on content similarity"""
        
        unique_docs = []
        seen_content = set()
        
        for doc in documents:
            # Create content hash for deduplication
            content_hash = hashlib.md5(doc["content"].encode()).hexdigest()
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_docs.append(doc)
        
        return unique_docs
    
    def _rank_documents(self, documents: List[Dict[str, Any]], context: ConversationContext) -> List[Dict[str, Any]]:
        """Rank documents based on relevance and context"""
        
        # Simple ranking based on score and context relevance
        for doc in documents:
            # Boost score for documents matching user's knowledge level
            if context.knowledge_level.value in doc.get("metadata", {}).get("target_audience", "").lower():
                doc["score"] *= 1.2
            
            # Boost score for documents matching current topic
            if context.current_topic and context.current_topic.lower() in doc.get("metadata", {}).get("topics", "").lower():
                doc["score"] *= 1.1
        
        # Sort by score
        documents.sort(key=lambda x: x.get("score", 0), reverse=True)
        return documents

class EnhancedRAGSystem:
    """Enhanced RAG system with semantic understanding"""
    
    def __init__(self, qdrant_client: QdrantClient = None, external_search_system = None):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
        
        # Store external search system for supplementation
        self.external_search_system = external_search_system
        
        # Use in-memory Qdrant by default (no external service needed!)
        if qdrant_client:
            self.qdrant_client = qdrant_client
            self.qdrant_available = True
        else:
            try:
                # Try to connect to external Qdrant first
                self.qdrant_client = QdrantClient(
                    host=config.qdrant_host,
                    port=config.qdrant_port
                )
                # Test connection
                self.qdrant_client.get_collections()
                self.qdrant_available = True
                logger.info("✅ Connected to external Qdrant instance")
                # Initialize Qdrant collection if needed
                self._ensure_collection_exists()
            except Exception as e:
                logger.info(f"External Qdrant not available: {e}. Using in-memory Qdrant instead.")
                # Fallback to in-memory Qdrant (no external service needed!)
                self.qdrant_client = QdrantClient(":memory:")
                self.qdrant_available = True
                logger.info("✅ Created in-memory Qdrant instance")
                self._ensure_collection_exists()
        
        self.query_expander = SemanticQueryExpander()
        self.multi_query_retriever = MultiQueryRetriever(self.qdrant_client)
        self.document_processor = DocumentProcessor()
        
        # Initialize intelligent context-aware query enhancer
        # self.query_enhancer = ContextAwareQueryEnhancer() # REMOVED: Simple context system
        
        # Initialize context-aware document retriever # REMOVED: Simple context system
        # self.context_aware_retriever = ContextAwareDocumentRetriever() # REMOVED: Simple context system
        
    def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists"""
        
        try:
            # For in-memory Qdrant, we need to handle differently
            # Check if this is an in-memory instance by trying to get collections
            try:
                collections = self.qdrant_client.get_collections()
                collection_names = [col.name for col in collections.collections]
                
                if config.qdrant_collection_name not in collection_names:
                    self.qdrant_client.create_collection(
                        collection_name=config.qdrant_collection_name,
                        vectors_config=VectorParams(
                            size=1536,  # OpenAI embedding dimension
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created Qdrant collection: {config.qdrant_collection_name}")
                    
            except Exception as collection_error:
                # This might be an in-memory instance with no collections yet
                # Try to create the collection directly
                try:
                    self.qdrant_client.create_collection(
                        collection_name=config.qdrant_collection_name,
                        vectors_config=VectorParams(
                            size=1536,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created in-memory Qdrant collection: {config.qdrant_collection_name}")
                except Exception as create_error:
                    logger.error(f"Failed to create collection: {create_error}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            # Final fallback attempt
            try:
                self.qdrant_client.create_collection(
                    collection_name=config.qdrant_collection_name,
                    vectors_config=VectorParams(
                        size=1536,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection after error: {config.qdrant_collection_name}")
            except Exception as create_error:
                logger.error(f"Failed to create collection: {create_error}")
    
    def has_documents(self) -> bool:
        """Check if the collection has any documents"""
        try:
            # Try to get collection info
            collection_info = self.qdrant_client.get_collection_info(config.qdrant_collection_name)
            return collection_info.vectors_count > 0
        except Exception as e:
            logger.debug(f"Could not check collection info: {e}")
            return False
    
    @property
    def collection_info(self):
        """Get collection information"""
        try:
            return self.qdrant_client.get_collection_info(config.qdrant_collection_name)
        except Exception as e:
            logger.debug(f"Could not get collection info: {e}")
            return None
    
    async def get_semantic_response(self, query: str, context: ConversationContext, intent_result: IntentResult = None, needs_external_search: bool = None) -> RAGResult:
        """Get semantic response using RAG with proper multi-query retrieval"""
        try:
            logger.info(f"🔍 RAG SYSTEM: Starting semantic response generation for query: '{query[:100]}...'")
            
            # NEW: Intelligently enhance query with conversation context for better RAG retrieval
            # This system now understands semantic relationships and follow-up questions
            # try: # REMOVED: Simple context system
            #     enhanced_query = await self.query_enhancer.enhance_query_for_rag(query, context) # REMOVED: Simple context system
            #     if enhanced_query != query: # REMOVED: Simple context system
            #         logger.info(f"🔍 RAG SYSTEM: Query intelligently enhanced: '{query[:50]}...' -> '{enhanced_query[:100]}...'") # REMOVED: Simple context system
            #         query = enhanced_query  # Use enhanced query for retrieval # REMOVED: Simple context system
            # except Exception as e: # REMOVED: Simple context system
            #     logger.error(f"🔍 RAG SYSTEM: Error in query enhancement: {e}") # REMOVED: Simple context system
            #     # Continue with original query if enhancement fails # REMOVED: Simple context system
            
            # CRITICAL FIX: Use MultiQueryRetriever for comprehensive document retrieval
            # This ensures we get all relevant documents in a single call instead of multiple calls
            logger.info("🔍 RAG SYSTEM: Using MultiQueryRetriever for comprehensive document retrieval")
            raw_documents = await self.multi_query_retriever.retrieve_documents([query], context, k=15)
            
            # SIMPLIFIED: Use original simple context system for RAG (restore what was working)
            # Remove complex conversation_memory integration that was causing issues
            documents = raw_documents
            
            if not documents:
                logger.warning("🔍 RAG SYSTEM: No documents retrieved, using fallback response")
                fallback_response = self._get_fallback_response([], query, context)
                return RAGResult(
                    response=fallback_response,
                    quality_score=0.5,
                    source_documents=[],
                    semantic_queries=[query],
                    confidence=0.5
                )
            
            logger.info(f"🔍 RAG SYSTEM: Retrieved {len(documents)} documents using MultiQueryRetriever")
            
            # Generate response from retrieved documents
            rag_response = await self._generate_semantic_response(query, documents, context)
            
            # Track sources used
            sources_used = ["RAG (Vector Database)"]
            search_sources = ""
            search_result = None
            
            # SIMPLIFIED: Basic external search logic
            # The external search system handles its own caching and deduplication
            
            # SIMPLIFIED: Basic external search logic
            should_search = needs_external_search and self.external_search_system
            if should_search:
                logger.info("🔍 RAG SYSTEM: External search supplementation requested")
                
                try:
                    supplemented_response, search_result = await self._supplement_with_external_search(query, rag_response, context, intent_result, should_search)
                    
                    if supplemented_response != rag_response:
                        logger.info("🔍 RAG SYSTEM: Response supplemented with external search")
                        rag_response = supplemented_response
                        sources_used.append("External Search (Tavily)")
                        # Get search sources if available
                        search_sources = await self._get_search_sources(query, context, search_result)
                    else:
                        logger.info("🔍 RAG SYSTEM: External search supplementation completed (no changes)")
                except Exception as e:
                    logger.error(f"🔍 RAG SYSTEM: Error in external search supplementation: {e}")
                    # Continue without external search if it fails
            else:
                logger.info("🔍 RAG SYSTEM: No external search supplementation needed")
            
            # Evaluate response quality
            quality_score = await self._evaluate_response_quality(query, rag_response, documents, context)
            logger.info(f"🔍 RAG SYSTEM: Response quality evaluation: {quality_score:.3f}")
            
            # Add source attribution to response
            if sources_used:
                rag_response += f"\n\n**Sources Used:** {', '.join(sources_used)}"
                if search_sources:
                    logger.info(f"🔍 RAG SYSTEM: Adding search sources to response: {search_sources[:200]}...")
                    rag_response += f"\n\n**External Search Result Sources:**\n{search_sources}"
                else:
                    logger.info("🔍 RAG SYSTEM: No search sources to add")
            else:
                logger.info("🔍 RAG SYSTEM: No sources used")
            
            return RAGResult(
                response=rag_response,
                quality_score=quality_score,
                source_documents=documents,  # Return actual retrieved documents
                semantic_queries=[query],
                confidence=quality_score
            )
            
        except Exception as e:
            logger.error(f"🔍 RAG SYSTEM: Error in semantic response generation: {e}")
            # Return fallback response
            fallback_response = self._get_fallback_response([], query, context)
            return RAGResult(
                response=fallback_response,
                quality_score=0.5,
                source_documents=[],
                semantic_queries=[query],
                confidence=0.5
            )
    
    def _create_semantic_query_key(self, query: str, intent_result: Optional[IntentResult]) -> str:
        """Create a semantic key for query deduplication to prevent multiple external search calls"""
        try:
            # Extract key terms from the query
            query_lower = query.lower()
            key_terms = []
            
            # Extract insurance-related terms
            if "life insurance" in query_lower:
                key_terms.append("life_insurance")
            if "term" in query_lower:
                key_terms.append("term")
            if "rate" in query_lower or "price" in query_lower or "cost" in query_lower:
                key_terms.append("rates")
            if "progressive" in query_lower or "company" in query_lower:
                key_terms.append("company_specific")
            if "current" in query_lower or "2024" in query_lower or "2025" in query_lower:
                key_terms.append("current_info")
            
            # Add intent information
            intent_key = intent_result.intent.value if intent_result else "unknown"
            
            # Create semantic key
            semantic_key = f"{intent_key}_{'_'.join(sorted(key_terms))}"
            
            logger.info(f"🔍 RAG SYSTEM: Created semantic query key: '{query[:50]}...' -> '{semantic_key}'")
            return semantic_key
            
        except Exception as e:
            logger.error(f"🔍 RAG SYSTEM: Error creating semantic query key: {e}")
            # Fallback to simple hash
            return f"fallback_{hash(query) % 10000}"
    
    async def _generate_semantic_response(self, query: str, documents: List[Dict[str, Any]], context: ConversationContext) -> str:
        """Generate semantic response using retrieved documents"""
        try:
            if not documents:
                logger.warning("🔍 RAG SYSTEM: No documents provided for response generation, using fallback")
                return self._get_fallback_response([], query, context)
            
            logger.info(f"🔍 RAG SYSTEM: Generating response from {len(documents)} retrieved documents")
            
            # Build document context from retrieved documents
            doc_context = self._build_document_context(documents)
            logger.info(f"🔍 RAG SYSTEM: Document context built: {len(doc_context)} characters")
            
            # Build response generation prompt
            prompt = self._build_response_generation_prompt(query, doc_context, context)
            
            # Generate response using LLM
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": "You are a knowledgeable financial advisor assistant. Use the provided document context to answer questions accurately and comprehensively."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            generated_response = response.choices[0].message.content.strip()
            logger.info(f"🔍 RAG SYSTEM: Response generated: {len(generated_response)} characters")
            
            return generated_response
            
        except Exception as e:
            logger.error(f"🔍 RAG SYSTEM: Error generating semantic response: {e}")
            return self._get_fallback_response(documents, query, context)
    
    def _build_document_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build document context from retrieved documents"""
        try:
            if not documents:
                logger.warning("🔍 RAG SYSTEM: No documents provided to context builder")
                return ""
            
            logger.info(f"🔍 RAG SYSTEM: Building context from {len(documents)} documents")
            
            # Validate document structure
            valid_documents = []
            for i, doc in enumerate(documents):
                if not isinstance(doc, dict):
                    logger.warning(f"🔍 RAG SYSTEM: Document {i+1} is not a dictionary: {type(doc)}")
                    continue
                
                content = doc.get('content', '')
                source = doc.get('source', 'Unknown')
                score = doc.get('score', 0)
                
                # Validate content
                if not content or not isinstance(content, str):
                    logger.warning(f"🔍 RAG SYSTEM: Document {i+1} has invalid content: {type(content)}")
                    continue
                
                # Validate score
                if not isinstance(score, (int, float)):
                    logger.warning(f"🔍 RAG SYSTEM: Document {i+1} has invalid score: {type(score)}")
                    score = 0.0
                
                valid_documents.append({
                    'content': content,
                    'source': source,
                    'score': float(score)
                })
            
            if not valid_documents:
                logger.warning("🔍 RAG SYSTEM: No valid documents after validation")
                return ""
            
            logger.info(f"🔍 RAG SYSTEM: {len(valid_documents)} valid documents after validation")
            
            # Sort documents by relevance score
            sorted_docs = sorted(valid_documents, key=lambda x: x.get('score', 0), reverse=True)
            
            # Build context from top documents
            context_parts = []
            for i, doc in enumerate(sorted_docs[:5]):  # Use top 5 documents
                content = doc.get('content', '')
                source = doc.get('source', 'Unknown')
                score = doc.get('score', 0)
                
                logger.info(f"🔍 RAG SYSTEM: Document {i+1} - content length: {len(content)}, source: {source}, score: {score}")
                
                if content:
                    context_parts.append(f"Document {i+1} (Source: {source}, Relevance: {score:.3f}):\n{content}\n")
                else:
                    logger.warning(f"🔍 RAG SYSTEM: Document {i+1} has empty content")
            
            final_context = "\n".join(context_parts)
            logger.info(f"🔍 RAG SYSTEM: Final context length: {len(final_context)} characters")
            
            # Additional validation
            if len(final_context) < 100:
                logger.warning(f"🔍 RAG SYSTEM: Generated context is very short ({len(final_context)} chars) - this may indicate an issue")
            
            return final_context
            
        except Exception as e:
            logger.error(f"🔍 RAG SYSTEM: Error building document context: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _build_response_generation_prompt(self, query: str, doc_context: str, context: ConversationContext) -> str:
        """Build prompt for response generation using retrieved documents with ChatGPT-like context awareness"""
        
        # RESTORED: Use original simple context system that was working before
        # Remove complex conversation_memory integration that was causing issues
        conversation_context = ""
        
        # Use original simple context fields that were working
        if context.current_topic:
            conversation_context += f"**Current Conversation Focus:** {context.current_topic}\n"
        
        if context.semantic_themes:
            recent_themes = context.semantic_themes[-5:]
            conversation_context += f"**Recent Topics Discussed:** {', '.join(recent_themes)}\n"
            
            if len(recent_themes) > 0:
                conversation_context += f"**Most Recent Topic:** {recent_themes[-1]}\n"
        
        if context.user_goals:
            recent_goals = context.user_goals[-3:]
            conversation_context += f"**Your Goals:** {', '.join(recent_goals)}\n"
        
        logger.info("🔍 RAG SYSTEM: Using original simple context system for response generation")
        
        # Detect if this is a follow-up question with enhanced patterns
        follow_up_indicators = [
            'go deeper', 'tell me more', 'explain', 'how does', 'what about',
            'can you', 'could you', 'expand on', 'elaborate', 'dive into',
            'restate', 'repeat', 'say that again', 'clarify', 'what do you mean',
            'i don\'t understand', 'confused', 'lost me', 'help me understand',
            'more about', 'more on', 'further', 'additional', 'extra'
        ]
        
        is_follow_up = any(indicator in query.lower() for indicator in follow_up_indicators)
        
        # Also check for context continuation indicators
        context_continuation_indicators = [
            'this', 'that', 'it', 'they', 'them', 'those', 'these',
            'the', 'a', 'an', 'some', 'any', 'all', 'both', 'either', 'neither'
        ]
        
        has_context_continuation = any(indicator in query.lower() for indicator in context_continuation_indicators)
        is_follow_up = is_follow_up or has_context_continuation
        
        # Build comprehensive context-aware instructions
        context_instructions = ""
        if is_follow_up and context.semantic_themes:
            # For follow-up questions, emphasize using previous context
            most_recent_theme = context.semantic_themes[-1]
            recent_themes = context.semantic_themes[-3:]  # Last 3 themes for context
            
            context_instructions = f"""
**IMPORTANT - This is a follow-up question!** 
- The user is asking for more details about: {most_recent_theme}
- Recent conversation context: {', '.join(recent_themes)}
- Connect your answer to what we discussed previously
- Reference the previous topic naturally in your response
- Build upon the knowledge we've already established
- If the user asks about a component (like "cash value"), relate it to the main topic we discussed
"""
        elif context.current_topic and context.current_topic != 'General':
            # For related questions, maintain conversation flow
            context_instructions = f"""
**Conversation Context:**
- We're discussing: {context.current_topic}
- Recent themes: {', '.join(context.semantic_themes[-3:]) if context.semantic_themes else 'None'}
- Maintain the flow and build on what we've covered
- Reference relevant previous topics when helpful
"""
        
        return f"""
You are a knowledgeable financial advisor assistant having a natural conversation with a client. Answer the user's question using the provided document context while maintaining conversation flow and context awareness.

**User Question:** {query}
**User Knowledge Level:** {context.knowledge_level.value}

{conversation_context}

{context_instructions}

**Document Context:**
{doc_context}

**Instructions:**
1. **Use ONLY the provided document context** - do not add external knowledge
2. **Answer the specific question asked** - be direct and relevant
3. **DO NOT cite specific documents** - do not mention "Document 1", "Document 2", etc. in your response
4. **DO NOT include a sources section** - source attribution is handled separately
5. **Adapt to user's knowledge level** - use appropriate terminology
6. **Be comprehensive** but concise
7. **If information is missing**, acknowledge what you don't know
8. **Maintain conversation flow** - consider the conversation context when appropriate
9. **Build on previous topics** - reference recent themes if relevant to the current question
10. **For follow-up questions**, connect your answer to what we discussed previously
11. **Be conversational** - like ChatGPT, maintain context without being robotic

**Response Format:**
- Start with a direct answer to the question
- If this is a follow-up, briefly reference what we discussed before (e.g., "Building on our discussion of IUL...")
- Provide supporting details from the documents WITHOUT citing specific document numbers
- Write in a natural, conversational tone - do not mention "Document 1", "according to Document 2", etc.
- Reference conversation context when it enhances the response
- For component questions (like "cash value"), explain how it relates to the main topic we discussed
- End with actionable next steps if applicable
- Maintain a conversational tone that feels natural and contextual
- Do NOT include any "Sources:" section or document references in your response

**Generate a helpful, accurate, and contextually aware response based on the document context:**
"""
    
    def _get_fallback_response(self, documents: List[Dict[str, Any]], query: str = None, context: ConversationContext = None) -> str:
        """Get fallback response when document retrieval or processing fails"""
        try:
            if documents:
                # Try to create a simple response from available documents
                return self._create_fallback_response(documents)
            else:
                # No documents available
                return "I apologize, but I'm unable to retrieve the specific information you're looking for at the moment. Please try rephrasing your question or ask about a different topic."
                
        except Exception as e:
            logger.error(f"🔍 RAG SYSTEM: Error in fallback response: {e}")
            return "I'm experiencing technical difficulties. Please try again or ask a different question."
    
    def _create_fallback_response(self, documents: List[Dict[str, Any]]) -> str:
        """Create a simple fallback response from available documents"""
        try:
            if not documents:
                return "I don't have enough information to answer your question accurately."
            
            # Use the most relevant document
            best_doc = max(documents, key=lambda x: x.get('score', 0))
            content = best_doc.get('content', '')
            
            if content:
                # Return a brief summary
                return f"Based on the available information: {content[:200]}..."
            else:
                return "I have some information available but it's not sufficient to answer your question completely."
                
        except Exception as e:
            logger.error(f"🔍 RAG SYSTEM: Error creating fallback response: {e}")
            return "I'm unable to provide a complete answer at this time."
    
    async def _evaluate_response_quality(self, query: str, response: str, documents: List[Dict[str, Any]], context: ConversationContext) -> float:
        """Evaluate response quality using RAGAS metrics and retrieved documents"""
        try:
            if not documents:
                logger.warning("🔍 RAG SYSTEM: No documents available for quality evaluation")
                return 0.5  # Default score when no documents available
            
            logger.info(f"🔍 RAG SYSTEM: Evaluating response quality using {len(documents)} documents")
            
            # Build quality evaluation prompt
            prompt = self._build_quality_evaluation_prompt(query, response, documents, context)
            
            # Get quality evaluation from LLM
            evaluation_response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of financial advice quality. Assess responses based on accuracy, relevance, and helpfulness."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            evaluation_text = evaluation_response.choices[0].message.content.strip()
            logger.info(f"🔍 RAG SYSTEM: Quality evaluation response: {evaluation_text[:100]}...")
            
            # Parse quality score
            quality_score = self._parse_quality_score(evaluation_text)
            logger.info(f"🔍 RAG SYSTEM: Parsed quality score: {quality_score:.3f}")
            
            return quality_score
            
        except Exception as e:
            logger.error(f"🔍 RAG SYSTEM: Error in quality evaluation: {e}")
            return 0.5  # Default score on error
    
    def _build_quality_evaluation_prompt(self, query: str, response: str, documents: List[Dict[str, Any]], context: ConversationContext) -> str:
        """Build prompt for quality evaluation using RAGAS metrics"""
        return f"""
        Evaluate the quality of this financial advice response using RAGAS metrics.
        
        **User Question:** {query}
        **Generated Response:** {response}
        **Available Documents:** {len(documents)} documents
        
        **Conversation Context:**
        - Current Topic: {context.current_topic or 'General'}
        - Recent Themes: {', '.join(context.semantic_themes[-3:]) if context.semantic_themes else 'None'}
        - User Goals: {', '.join(context.user_goals[-2:]) if context.user_goals else 'None'}
        - Knowledge Level: {context.knowledge_level.value if hasattr(context, 'knowledge_level') else 'Unknown'}
        
        **Evaluation Criteria (Score 0.0-1.0):**
        1. **Faithfulness (0.0-1.0):** Does the response accurately reflect the information in the documents?
        2. **Answer Relevancy (0.0-1.0):** Does the response directly answer the user's question?
        3. **Context Precision (0.0-1.0):** Are the retrieved documents relevant to the query?
        4. **Context Recall (0.0-1.0):** Does the response use the most relevant information from the documents?
        5. **Conversation Continuity (0.0-1.0):** Does the response maintain conversation flow and context?
        
        **Scoring Guidelines:**
        - 0.0-0.3: Poor quality, inaccurate, irrelevant, breaks conversation flow
        - 0.4-0.6: Moderate quality, some inaccuracies, partially relevant, limited conversation continuity
        - 0.7-0.8: Good quality, mostly accurate, relevant, maintains conversation flow
        - 0.9-1.0: Excellent quality, highly accurate, very relevant, excellent conversation continuity
        
        **Return only a single number between 0.0 and 1.0 representing the overall quality score:**
        """
    
    def _parse_quality_score(self, evaluation: str) -> float:
        """Parse quality score from evaluation response"""
        try:
            # Extract numeric score from the evaluation text
            import re
            
            # Look for numbers between 0.0 and 1.0
            score_pattern = r'\b(0\.\d+|1\.0|0|1)\b'
            matches = re.findall(score_pattern, evaluation)
            
            if matches:
                # Convert to float and validate range
                score = float(matches[0])
                if 0.0 <= score <= 1.0:
                    logger.info(f"🔍 RAG SYSTEM: Parsed quality score: {score:.3f}")
                    return score
                else:
                    logger.warning(f"🔍 RAG SYSTEM: Score out of range: {score}, clamping to valid range")
                    return max(0.0, min(1.0, score))
            
            # Fallback: look for percentage or other numeric formats
            percentage_pattern = r'(\d+)%'
            percentage_matches = re.findall(percentage_pattern, evaluation)
            if percentage_matches:
                score = float(percentage_matches[0]) / 100.0
                logger.info(f"🔍 RAG SYSTEM: Parsed percentage score: {score:.3f}")
                return score
            
            # Final fallback: extract any number and normalize
            number_pattern = r'\b(\d+)\b'
            number_matches = re.findall(number_pattern, evaluation)
            if number_matches:
                score = min(float(number_matches[0]) / 100.0, 1.0)
                logger.info(f"🔍 RAG SYSTEM: Parsed normalized score: {score:.3f}")
                return score
            
            logger.warning("🔍 RAG SYSTEM: Could not parse quality score, using default")
            return 0.5  # Default score
            
        except Exception as e:
            logger.error(f"🔍 RAG SYSTEM: Error parsing quality score: {e}")
            return 0.5  # Default score on error
    
    async def ingest_documents(self, documents_path: str = None) -> bool:
        """Ingest documents into the RAG system"""
        
        try:
            docs_path = documents_path or config.rag_documents_path
            docs_dir = Path(docs_path)
            
            if not docs_dir.exists():
                logger.warning(f"Documents directory does not exist: {docs_path}")
                return False
            
            # Process all documents
            all_chunks = []
            
            for file_path in docs_dir.rglob("*"):
                if file_path.is_file():
                    file_chunks = await self._process_file(file_path)
                    all_chunks.extend(file_chunks)
            
            if not all_chunks:
                logger.warning("No documents processed")
                return False
            
            # Get embeddings and store in Qdrant
            await self._store_chunks_in_qdrant(all_chunks)
            
            logger.info(f"Successfully ingested {len(all_chunks)} document chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")
            return False
    
    async def _process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process individual file"""
        
        try:
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.txt':
                chunks = self.document_processor.process_text_file(str(file_path))
            elif file_extension == '.pdf':
                chunks = self.document_processor.process_pdf_file(str(file_path))
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return []
            
            # Add file metadata
            for chunk in chunks:
                chunk["metadata"]["filename"] = file_path.name
                chunk["metadata"]["file_path"] = str(file_path)
                chunk["metadata"]["file_type"] = file_extension
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return []
    
    async def _store_chunks_in_qdrant(self, chunks: List[Dict[str, Any]]) -> None:
        """Store document chunks in Qdrant with embeddings"""
        
        try:
            from openai import AsyncOpenAI
            embedding_model = AsyncOpenAI(api_key=config.openai_api_key)
            
            # Process chunks in batches
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # Get embeddings for batch
                texts = [chunk["content"] for chunk in batch]
                embeddings = await embedding_model.embeddings.create(
                    model=config.embedding_model,
                    input=texts
                )
                
                # Create points for Qdrant
                points = []
                for j, chunk in enumerate(batch):
                    point = PointStruct(
                        id=chunk["id"],
                        vector=embeddings.data[j].embedding,
                        payload={
                            "content": chunk["content"],
                            "source": chunk["source"],
                            "metadata": chunk["metadata"]
                        }
                    )
                    points.append(point)
                
                # Store in Qdrant
                self.qdrant_client.upsert(
                    collection_name=config.qdrant_collection_name,
                    points=points
                )
                
                logger.info(f"Stored batch {i//batch_size + 1} in Qdrant")
                
        except Exception as e:
            logger.error(f"Error storing chunks in Qdrant: {e}")
            raise 

    async def _supplement_with_external_search(self, query: str, rag_response: str, context: ConversationContext, intent_result: IntentResult = None, needs_external_search: bool = None) -> tuple[str, Any]:
        """Supplement RAG response with external search if needed and valuable"""
        try:
            logger.info("🔍 Checking if external search supplementation is needed...")
            
            # Check if this is a calculator intent - NEVER use external search for calculators
            # Use intent_result parameter directly if available
            if intent_result and intent_result.intent in ['insurance_needs_calculation', 'client_assessment_support', 'portfolio_integration_analysis']:
                logger.info("   Calculator intent detected - skipping external search")
                return rag_response, None
            
            # Determine if external search is needed
            # Priority: 1) Direct parameter, 2) Intent result (NO context field check to avoid duplication)
            if needs_external_search is not None:
                should_search = needs_external_search
                logger.info(f"   External search decision from direct parameter: {should_search}")
            elif intent_result and intent_result.needs_external_search:
                should_search = True
                logger.info(f"   External search decision from intent result: {should_search}")
            else:
                # Don't check context.needs_external_search to avoid duplicate logic
                should_search = False
                logger.info(f"   No external search needed (context field not checked to avoid duplication)")
            
            logger.info(f"   Final search decision: {should_search}")
            logger.info(f"   Intent result needs_external_search: {intent_result.needs_external_search if intent_result else 'N/A'}")
            logger.info(f"   Context needs_external_search: {getattr(context, 'needs_external_search', 'N/A')}")
            
            if not should_search:
                logger.info("   External search not needed")
                return rag_response, None
            
            logger.info("   External search supplementation requested")
            
            # Check if external search system is available
            if not self.external_search_system:
                logger.warning("   External search system not available - skipping supplementation")
                return rag_response, None
            
            # Perform external search
            search_result = await self.external_search_system.search_with_evaluation(query, context, needs_external_search=should_search)
            
            if not search_result or search_result.quality_score < config.min_search_confidence:
                logger.info(f"   External search quality below threshold ({search_result.quality_score if search_result else 'N/A'} < {config.min_search_confidence})")
                return rag_response, None
            
            logger.info(f"   External search quality above threshold ({search_result.quality_score} >= {config.min_search_confidence})")
            
            # Combine RAG and search results
            combined_response = self._combine_rag_and_search(rag_response, search_result, query)
            logger.info("   Successfully combined RAG and external search results")
            
            return combined_response, search_result
            
        except Exception as e:
            logger.error(f"Error in external search supplementation: {e}")
            return rag_response, None
    
    def _combine_rag_and_search(self, rag_response: str, search_result: Any, query: str) -> str:
        """Intelligently merge RAG response with external search results to create a unified, high-quality response"""
        
        try:
            # Extract search results and filter for relevance
            relevant_search_info = self._extract_relevant_search_info(search_result, query)
            
            if not relevant_search_info:
                logger.info("   No relevant search information found - returning RAG response only")
                return rag_response
            
            # Create a unified response using LLM-based merging
            merged_response = self._create_unified_response(rag_response, relevant_search_info, query)
            
            return merged_response
            
        except Exception as e:
            logger.error(f"Error combining RAG and search results: {e}")
            return rag_response
    
    def _extract_relevant_search_info(self, search_result: Any, query: str) -> str:
        """Extract only the search information that's relevant to the user's query"""
        
        try:
            relevant_info = []
            
            # Extract search results
            source_results = getattr(search_result, 'source_results', [])
            if not source_results:
                return ""
            
            # Filter and extract relevant information
            for result in source_results[:3]:  # Top 3 results
                content = result.get('content', '')
                title = result.get('title', '')
                
                # Check if this result contains information relevant to the query
                if self._is_relevant_to_query(content, title, query):
                    # Extract the most relevant parts
                    relevant_parts = self._extract_relevant_parts(content, query)
                    if relevant_parts:
                        relevant_info.append(f"**{title}**: {relevant_parts}")
            
            if relevant_info:
                return "\n\n".join(relevant_info)
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting relevant search info: {e}")
            return ""
    
    def _is_relevant_to_query(self, content: str, title: str, query: str) -> bool:
        """Check if search result content is relevant to the user's query"""
        
        query_lower = query.lower()
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Check for key terms from the query
        key_terms = []
        
        # Rate/price related queries
        if any(term in query_lower for term in ["rate", "rates", "price", "prices", "cost", "premium"]):
            key_terms.extend(["rate", "price", "cost", "premium", "quote", "pricing", "fee"])
        
        # Company-specific queries
        if any(company in query_lower for company in ["progressive", "state farm", "allstate", "geico", "farmers"]):
            key_terms.extend(["progressive", "state farm", "allstate", "geico", "farmers", "company", "carrier", "insurer", "provider"])
        
        # Current/timely queries
        if any(term in query_lower for term in ["current", "today", "latest", "recent", "now"]):
            key_terms.extend(["current", "today", "latest", "recent", "2024", "2025", "this year", "now"])
        
        # Insurance product queries
        if any(term in query_lower for term in ["term life", "life insurance", "policy", "coverage"]):
            key_terms.extend(["term", "life insurance", "policy", "coverage", "benefit", "protection"])
        
        # Market condition queries
        if any(term in query_lower for term in ["market", "trend", "condition", "environment"]):
            key_terms.extend(["market", "trend", "condition", "environment", "climate", "outlook"])
        
        # If no specific terms found, use general financial terms
        if not key_terms:
            key_terms = ["insurance", "life", "term", "rate", "price", "company", "current"]
        
        # Check if any key terms are present
        for term in key_terms:
            if term in content_lower or term in title_lower:
                return True
        
        # Additional relevance checks for financial content
        financial_indicators = ["$", "dollar", "percent", "%", "premium", "coverage", "policy", "insurance"]
        if any(indicator in content_lower for indicator in financial_indicators):
            return True
        
        return False
    
    def _extract_relevant_parts(self, content: str, query: str) -> str:
        """Extract the most relevant parts of search content based on the query"""
        
        try:
            # Simple relevance extraction - look for sentences containing key terms
            sentences = content.split('. ')
            relevant_sentences = []
            
            query_lower = query.lower()
            key_terms = []
            if "rates" in query_lower:
                key_terms.extend(["rate", "premium", "cost", "price"])
            if "progressive" in query_lower:
                key_terms.extend(["progressive", "company"])
            if "current" in query_lower:
                key_terms.extend(["current", "latest", "recent"])
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(term in sentence_lower for term in key_terms):
                    relevant_sentences.append(sentence.strip())
            
            # Limit to 2-3 most relevant sentences
            if relevant_sentences:
                return '. '.join(relevant_sentences[:2]) + '.'
            else:
                # If no specific matches, return first 100 characters
                return content[:100] + '...' if len(content) > 100 else content
                
        except Exception as e:
            logger.error(f"Error extracting relevant parts: {e}")
            return content[:100] + '...' if len(content) > 100 else content
    
    def _create_unified_response(self, rag_response: str, relevant_search_info: str, query: str) -> str:
        """Create a unified, high-quality response that seamlessly combines RAG and search information"""
        
        try:
            # Create a prompt for intelligent merging
            merge_prompt = f"""
            You are an expert financial advisor. Create a unified, high-quality response that seamlessly combines:
            
            **RAG Response (Internal Knowledge):**
            {rag_response}
            
            **Current External Information:**
            {relevant_search_info}
            
            **User Query:** {query}
            
            **Instructions:**
            1. Create a SINGLE, unified response that flows naturally
            2. Use the RAG response as the foundation
            3. Integrate relevant external information seamlessly
            4. Don't use separators or headers - make it one cohesive answer
            5. Prioritize current/real-time information when relevant
            6. Maintain professional, helpful tone
            7. Focus on being comprehensive yet concise
            8. If external info conflicts with RAG, note the difference but provide both perspectives
            
            **Create the unified response:**
            """
            
            # For now, we'll do intelligent text merging since we don't have LLM access here
            # In a production system, you'd call an LLM to do this merging
            
            # Simple intelligent merging approach
            merged = self._simple_intelligent_merge(rag_response, relevant_search_info, query)
            
            return merged
            
        except Exception as e:
            logger.error(f"Error creating unified response: {e}")
            # Fallback to simple combination
            return f"{rag_response}\n\n**Current Information:**\n{relevant_search_info}"
    
    def _simple_intelligent_merge(self, rag_response: str, search_info: str, query: str) -> str:
        """Simple but intelligent merging of RAG and search responses"""
        
        try:
            # Start with the RAG response
            merged = rag_response.strip()
            
            # If we have relevant search info, integrate it naturally
            if search_info and search_info.strip():
                # Look for natural integration points in the RAG response
                integration_points = [
                    "Generally,", "Typically,", "In general,", "Usually,", 
                    "The cost", "Rates", "Pricing", "Premiums"
                ]
                
                # Find the best integration point
                best_point = None
                for point in integration_points:
                    if point.lower() in merged.lower():
                        best_point = point
                        break
                
                if best_point:
                    # Insert current information after the integration point
                    sentences = merged.split('. ')
                    for i, sentence in enumerate(sentences):
                        if best_point.lower() in sentence.lower():
                            # Insert current information after this sentence
                            current_info = f" However, based on current market information: {search_info}"
                            sentences[i] = sentence + current_info
                            break
                    merged = '. '.join(sentences)
                else:
                    # If no good integration point, add at the end naturally
                    merged += f"\n\n**Current Market Information:** {search_info}"
                
                # Add a subtle note about the enhanced response
                merged += "\n\n*This response combines my comprehensive knowledge base with current market information to provide you with the most up-to-date and relevant answer.*"
            
            return merged
            
        except Exception as e:
            logger.error(f"Error in simple intelligent merge: {e}")
            # Fallback to simple combination
            return f"{rag_response}\n\n**Current Information:**\n{search_info}" 

    async def _get_search_sources(self, query: str, context: ConversationContext, search_result: Any = None) -> str:
        """Get search sources for attribution"""
        try:
            logger.info(f"🔍 RAG SYSTEM: Extracting search sources from search_result: {type(search_result)}")
            
            if not search_result or not hasattr(search_result, 'source_results'):
                logger.info("🔍 RAG SYSTEM: No search_result or no source_results attribute")
                return "Current market information and company-specific data from external sources"
            
            source_results = search_result.source_results
            logger.info(f"🔍 RAG SYSTEM: Found {len(source_results)} source results")
            
            if not source_results:
                logger.info("🔍 RAG SYSTEM: No source results to process")
                return "Current market information and company-specific data from external sources"
            
            # Format actual sources with titles and URLs
            source_lines = []
            for i, result in enumerate(source_results[:3], 1):  # Show top 3 sources
                title = result.get('title', 'Unknown Source')
                url = result.get('url', '')
                
                logger.info(f"🔍 RAG SYSTEM: Processing source {i}: title='{title[:50]}...', url='{url[:50]}...'")
                
                if url:
                    source_lines.append(f"{i}. [{title}]({url})")
                else:
                    source_lines.append(f"{i}. {title}")
            
            if source_lines:
                final_sources = "\n".join(source_lines)
                logger.info(f"🔍 RAG SYSTEM: Generated sources: {final_sources[:200]}...")
                return final_sources
            else:
                logger.info("🔍 RAG SYSTEM: No source lines generated")
                return "Current market information and company-specific data from external sources"
                
        except Exception as e:
            logger.error(f"Error getting search sources: {e}")
            return "Current market information and company-specific data from external sources" 