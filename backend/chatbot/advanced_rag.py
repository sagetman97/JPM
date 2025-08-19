import logging
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from .schemas import RAGResult, ConversationContext
from .config import config

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
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
    
    async def expand_query_semantically(self, query: str, context: ConversationContext) -> List[str]:
        """Expand query semantically based on context and intent"""
        
        try:
            prompt = self._build_expansion_prompt(query, context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            expanded_queries = self._parse_expanded_queries(response.choices[0].message.content)
            return expanded_queries
            
        except Exception as e:
            logger.error(f"Error expanding query semantically: {e}")
            return [query]  # Fallback to original query
    
    def _build_expansion_prompt(self, query: str, context: ConversationContext) -> str:
        """Build prompt for semantic query expansion"""
        
        return f"""
        Expand this query semantically to capture the full intent and related concepts:
        
        **Original Query:** "{query}"
        
        **Conversation Context:**
        - User's knowledge level: {context.knowledge_level.value}
        - Previous questions: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        - Current focus: {context.current_topic or 'General'}
        
        **Semantic Expansion Required:**
        - What related concepts should be included?
        - What underlying questions might they have?
        - What context would make this more comprehensive?
        - What financial planning aspects are relevant?
        
        **Generate 3-5 semantically related queries that capture the full scope of their intent.**
        
        **Return as JSON array:**
        ["expanded query 1", "expanded query 2", "expanded query 3"]
        
        **Focus on:**
        - Life insurance concepts and products
        - Financial planning strategies
        - Risk management approaches
        - Investment and portfolio considerations
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
    """Retrieves documents using multiple expanded queries"""
    
    def __init__(self, qdrant_client: QdrantClient = None):
        self.qdrant_client = qdrant_client
        self.collection_name = config.qdrant_collection_name if qdrant_client else None
    
    async def retrieve_documents(self, queries: List[str], context: ConversationContext, k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve documents using multiple queries"""
        
        try:
            all_documents = []
            
            for query in queries:
                # Get embedding for query
                embedding = await self._get_query_embedding(query)
                
                # Search in Qdrant
                search_results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=embedding,
                    limit=k,
                    with_payload=True
                )
                
                # Convert to document format
                for result in search_results:
                    doc = {
                        "id": result.id,
                        "content": result.payload.get("content", ""),
                        "source": result.payload.get("source", ""),
                        "metadata": result.payload.get("metadata", {}),
                        "score": result.score
                    }
                    all_documents.append(doc)
            
            # Deduplicate and rank documents
            unique_docs = self._deduplicate_documents(all_documents)
            ranked_docs = self._rank_documents(unique_docs, context)
            
            return ranked_docs[:k]
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    async def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for query using OpenAI"""
        
        try:
            from openai import OpenAI
            embedding_model = OpenAI(
                api_key=config.openai_api_key
            )
            
            response = embedding_model.embeddings.create(
                model=config.embedding_model,
                input=query
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error getting query embedding: {e}")
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
    
    def __init__(self, qdrant_client: QdrantClient = None):
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
        
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
        
        self.query_expander = SemanticQueryExpander()
        self.retriever = MultiQueryRetriever(self.qdrant_client)
        self.document_processor = DocumentProcessor()
        
    def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists"""
        
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.qdrant_client.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.qdrant_client.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.qdrant_client.collection_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
    
    async def get_semantic_response(self, query: str, context: ConversationContext) -> RAGResult:
        """Get response using semantic understanding"""
        
        try:
            # Semantic query expansion
            expanded_queries = await self.query_expander.expand_query_semantically(query, context)
            logger.info(f"Expanded queries: {expanded_queries}")
            
            # Semantic document retrieval
            relevant_docs = await self.retriever.retrieve_documents(expanded_queries, context)
            logger.info(f"Retrieved {len(relevant_docs)} relevant documents")
            
            if not relevant_docs:
                return await self._get_fallback_response(query, context)
            
            # Semantic response generation
            response = await self._generate_semantic_response(query, relevant_docs, context)
            
            # Semantic quality evaluation
            quality_score = await self._evaluate_response_quality(query, response, relevant_docs, context)
            
            return RAGResult(
                response=response,
                quality_score=quality_score,
                source_documents=relevant_docs,
                semantic_queries=expanded_queries
            )
            
        except Exception as e:
            logger.error(f"Error in semantic RAG: {e}")
            return await self._get_fallback_response(query, context)
    
    async def _generate_semantic_response(self, query: str, documents: List[Dict[str, Any]], context: ConversationContext) -> str:
        """Generate response using retrieved documents and semantic understanding"""
        
        try:
            # Prepare context from documents
            doc_context = "\n\n".join([f"Source: {doc['source']}\n{doc['content']}" for doc in documents[:5]])
            
            prompt = self._build_response_generation_prompt(query, doc_context, context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating semantic response: {e}")
            # Fallback to simple document summary
            return self._create_fallback_response(documents)
    
    def _build_response_generation_prompt(self, query: str, doc_context: str, context: ConversationContext) -> str:
        """Build prompt for response generation"""
        
        return f"""
        Generate a comprehensive, helpful response to this financial question using the provided knowledge base information:
        
        **User Question:** "{query}"
        
        **Knowledge Base Information:**
        {doc_context}
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'General'}
        - Previous Themes: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        
        **Response Requirements:**
        1. **Direct Answer**: Provide a clear, direct answer to their question
        2. **Educational Value**: Explain relevant concepts and principles
        3. **Context Awareness**: Consider their knowledge level and previous questions
        4. **Actionable Insights**: Provide practical next steps or considerations
        5. **Professional Tone**: Use appropriate financial advisory language
        6. **Compliance**: Include appropriate disclaimers and caveats
        
        **Response Guidelines:**
        - Be specific and actionable
        - Reference the knowledge base when possible
        - Match the user's knowledge level
        - Focus on life insurance and financial planning
        - Provide educational value, not specific financial advice
        
        **Generate a comprehensive, helpful response:**
        """
    
    def _create_fallback_response(self, documents: List[Dict[str, Any]]) -> str:
        """Create fallback response when LLM generation fails"""
        
        if not documents:
            return "I don't have specific information on that topic. Please consult with a licensed financial professional for personalized advice."
        
        # Simple summary of available information
        summary = "Based on my knowledge base, here's what I found:\n\n"
        
        for i, doc in enumerate(documents[:3], 1):
            summary += f"{i}. {doc['content'][:200]}...\n\n"
        
        summary += "For more detailed information or personalized advice, please consult with a licensed financial professional."
        
        return summary
    
    async def _evaluate_response_quality(self, query: str, response: str, documents: List[Dict[str, Any]], context: ConversationContext) -> float:
        """Evaluate response quality using semantic understanding"""
        
        try:
            prompt = self._build_quality_evaluation_prompt(query, response, documents, context)
            
            evaluation = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            quality_score = self._parse_quality_score(evaluation.choices[0].message.content)
            return quality_score
            
        except Exception as e:
            logger.error(f"Error evaluating response quality: {e}")
            return 0.7  # Default quality score
    
    def _build_quality_evaluation_prompt(self, query: str, response: str, documents: List[Dict[str, Any]], context: ConversationContext) -> str:
        """Build prompt for quality evaluation"""
        
        return f"""
        Evaluate the quality of this response to a financial question:
        
        **User Question:** "{query}"
        
        **Generated Response:** "{response}"
        
        **Source Documents Used:**
        {chr(10).join([f"- {doc['source']}: {doc['content'][:100]}..." for doc in documents[:3]])}
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'General'}
        
        **Quality Criteria (Rate 0-1 for each):**
        1. **Relevance**: Does the response directly address the question?
        2. **Accuracy**: Is the information correct and reliable?
        3. **Completeness**: Does it cover the full scope of the question?
        4. **Clarity**: Is the response clear and understandable?
        5. **Educational Value**: Does it provide useful insights?
        6. **Context Appropriateness**: Does it match the user's knowledge level?
        
        **Return JSON with scores and overall quality:**
        {{
            "relevance": 0.9,
            "accuracy": 0.8,
            "completeness": 0.7,
            "clarity": 0.9,
            "educational_value": 0.8,
            "context_appropriateness": 0.9,
            "overall_quality": 0.83
        }}
        """
    
    def _parse_quality_score(self, evaluation: str) -> float:
        """Parse quality evaluation response"""
        
        try:
            start_idx = evaluation.find('{')
            end_idx = evaluation.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = evaluation[start_idx:end_idx]
                eval_data = json.loads(json_str)
                
                return float(eval_data.get("overall_quality", 0.7))
            
        except Exception as e:
            logger.error(f"Error parsing quality score: {e}")
        
        return 0.7  # Default quality score
    
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
            from openai import OpenAI
            embedding_model = OpenAI(api_key=config.openai_api_key)
            
            # Process chunks in batches
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # Get embeddings for batch
                texts = [chunk["content"] for chunk in batch]
                embeddings = embedding_model.embeddings.create(
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
                    collection_name=self.qdrant_client.collection_name,
                    points=points
                )
                
                logger.info(f"Stored batch {i//batch_size + 1} in Qdrant")
                
        except Exception as e:
            logger.error(f"Error storing chunks in Qdrant: {e}")
            raise 