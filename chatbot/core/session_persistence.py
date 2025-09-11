"""
Session persistence system using Qdrant for storing and retrieving chat sessions.
Handles both in-memory fallback and Qdrant-based persistence.
"""

import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from .config import config
from .schemas import ChatSession, ConversationContext, ChatMessage, MessageType

logger = logging.getLogger(__name__)

class SessionPersistenceManager:
    """Manages session persistence using Qdrant with in-memory fallback"""
    
    def __init__(self, qdrant_client: QdrantClient = None):
        self.qdrant_client = qdrant_client
        self.collection_name = config.qdrant_sessions_collection
        self.use_qdrant = qdrant_client is not None
        
        # In-memory fallback storage
        self.memory_sessions: Dict[str, ChatSession] = {}
        
        if self.use_qdrant:
            self._ensure_sessions_collection_exists()
            logger.info("✅ Session persistence using Qdrant")
        else:
            logger.info("🔧 Session persistence using in-memory storage")
    
    def _ensure_sessions_collection_exists(self):
        """Ensure sessions collection exists in Qdrant"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding dimension for session context
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created sessions collection: {self.collection_name}")
            else:
                logger.info(f"✅ Sessions collection exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error ensuring sessions collection exists: {e}")
            # Fallback to in-memory
            self.use_qdrant = False
            logger.warning("🔧 Falling back to in-memory session storage")
    
    async def save_session(self, session: ChatSession) -> bool:
        """Save a chat session to persistent storage"""
        try:
            if self.use_qdrant:
                return await self._save_session_to_qdrant(session)
            else:
                return self._save_session_to_memory(session)
        except Exception as e:
            logger.error(f"❌ Error saving session {session.session_id}: {e}")
            return False
    
    async def _save_session_to_qdrant(self, session: ChatSession) -> bool:
        """Save session to Qdrant"""
        try:
            # Convert session to JSON for storage
            session_data = self._session_to_dict(session)
            
            # Create a simple embedding from session context (for searchability)
            context_text = f"{session.context.current_topic or ''} {session.context.knowledge_level.value} {' '.join(session.context.user_goals)}"
            context_embedding = await self._get_context_embedding(context_text)
            
            # Create point for Qdrant
            point = PointStruct(
                id=session.session_id,
                vector=context_embedding,
                payload={
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "session_data": session_data,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "status": session.status,
                    "context_topic": session.context.current_topic,
                    "knowledge_level": session.context.knowledge_level.value,
                    "user_goals": session.context.user_goals
                }
            )
            
            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"✅ Saved session {session.session_id} to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving session to Qdrant: {e}")
            return False
    
    def _save_session_to_memory(self, session: ChatSession) -> bool:
        """Save session to in-memory storage"""
        try:
            self.memory_sessions[session.session_id] = session
            logger.debug(f"✅ Saved session {session.session_id} to memory")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving session to memory: {e}")
            return False
    
    async def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load a chat session from persistent storage"""
        try:
            if self.use_qdrant:
                return await self._load_session_from_qdrant(session_id)
            else:
                return self._load_session_from_memory(session_id)
        except Exception as e:
            logger.error(f"❌ Error loading session {session_id}: {e}")
            return None
    
    async def _load_session_from_qdrant(self, session_id: str) -> Optional[ChatSession]:
        """Load session from Qdrant"""
        try:
            # Search for session by ID
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True
            )
            
            if results[0]:  # results is (points, next_page_offset)
                points = results[0]
                if points:
                    point = points[0]
                    session_data = point.payload.get("session_data", {})
                    return self._dict_to_session(session_data)
            
            logger.debug(f"Session {session_id} not found in Qdrant")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error loading session from Qdrant: {e}")
            return None
    
    def _load_session_from_memory(self, session_id: str) -> Optional[ChatSession]:
        """Load session from in-memory storage"""
        try:
            session = self.memory_sessions.get(session_id)
            if session:
                logger.debug(f"✅ Loaded session {session_id} from memory")
            else:
                logger.debug(f"Session {session_id} not found in memory")
            return session
        except Exception as e:
            logger.error(f"❌ Error loading session from memory: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session from persistent storage"""
        try:
            if self.use_qdrant:
                return await self._delete_session_from_qdrant(session_id)
            else:
                return self._delete_session_from_memory(session_id)
        except Exception as e:
            logger.error(f"❌ Error deleting session {session_id}: {e}")
            return False
    
    async def _delete_session_from_qdrant(self, session_id: str) -> bool:
        """Delete session from Qdrant"""
        try:
            # Find the point ID for this session
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=False
            )
            
            if results[0]:  # results is (points, next_page_offset)
                points = results[0]
                if points:
                    point_id = points[0].id
                    self.qdrant_client.delete(
                        collection_name=self.collection_name,
                        points_selector=[point_id]
                    )
                    logger.debug(f"✅ Deleted session {session_id} from Qdrant")
                    return True
            
            logger.debug(f"Session {session_id} not found for deletion")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error deleting session from Qdrant: {e}")
            return False
    
    def _delete_session_from_memory(self, session_id: str) -> bool:
        """Delete session from in-memory storage"""
        try:
            if session_id in self.memory_sessions:
                del self.memory_sessions[session_id]
                logger.debug(f"✅ Deleted session {session_id} from memory")
                return True
            else:
                logger.debug(f"Session {session_id} not found for deletion")
                return False
        except Exception as e:
            logger.error(f"❌ Error deleting session from memory: {e}")
            return False
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions from persistent storage"""
        try:
            if self.use_qdrant:
                return await self._cleanup_old_sessions_from_qdrant(max_age_hours)
            else:
                return self._cleanup_old_sessions_from_memory(max_age_hours)
        except Exception as e:
            logger.error(f"❌ Error cleaning up old sessions: {e}")
            return 0
    
    async def _cleanup_old_sessions_from_qdrant(self, max_age_hours: int) -> int:
        """Clean up old sessions from Qdrant"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            cutoff_iso = cutoff_time.isoformat()
            
            # Find old sessions
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="last_activity",
                            match=MatchValue(value=cutoff_iso),
                            range={"lt": cutoff_iso}
                        )
                    ]
                ),
                limit=1000,  # Process in batches
                with_payload=False
            )
            
            if results[0]:  # results is (points, next_page_offset)
                points = results[0]
                if points:
                    point_ids = [point.id for point in points]
                    self.qdrant_client.delete(
                        collection_name=self.collection_name,
                        points_selector=point_ids
                    )
                    logger.info(f"✅ Cleaned up {len(points)} old sessions from Qdrant")
                    return len(points)
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old sessions from Qdrant: {e}")
            return 0
    
    def _cleanup_old_sessions_from_memory(self, max_age_hours: int) -> int:
        """Clean up old sessions from in-memory storage"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            sessions_to_remove = []
            
            for session_id, session in self.memory_sessions.items():
                if session.last_activity < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.memory_sessions[session_id]
            
            if sessions_to_remove:
                logger.info(f"✅ Cleaned up {len(sessions_to_remove)} old sessions from memory")
            
            return len(sessions_to_remove)
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old sessions from memory: {e}")
            return 0
    
    def _session_to_dict(self, session: ChatSession) -> Dict[str, Any]:
        """Convert ChatSession to dictionary for storage"""
        try:
            return {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "messages": [
                    {
                        "id": msg.id,
                        "type": msg.type.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "files": msg.files or [],
                        "metadata": msg.metadata or {}
                    }
                    for msg in session.messages
                ],
                "context": {
                    "session_id": session.context.session_id,
                    "user_id": session.context.user_id,
                    "knowledge_level": session.context.knowledge_level.value,
                    "user_goals": session.context.user_goals,
                    "current_topic": session.context.current_topic,
                    "previous_calculations": session.context.previous_calculations,
                    "client_context": session.context.client_context,
                    "needs_external_search": session.context.needs_external_search,
                    "calculator_session": session.context.calculator_session,
                    "calculator_type": session.context.calculator_type.value if session.context.calculator_type else None,
                    "calculator_state": session.context.calculator_state,
                    "created_at": session.context.created_at.isoformat(),
                    "updated_at": session.context.updated_at.isoformat(),
                    "follow_up_result": self._follow_up_result_to_dict(session.context.follow_up_result),
                    "suggested_context_window": session.context.suggested_context_window,
                    "last_follow_up_topics": session.context.last_follow_up_topics
                },
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "status": session.status,
                "uploaded_files": session.uploaded_files
            }
        except Exception as e:
            logger.error(f"❌ Error converting session to dict: {e}")
            return {}
    
    def _dict_to_session(self, session_data: Dict[str, Any]) -> Optional[ChatSession]:
        """Convert dictionary to ChatSession"""
        try:
            # Convert messages
            messages = []
            for msg_data in session_data.get("messages", []):
                message = ChatMessage(
                    id=msg_data["id"],
                    type=MessageType(msg_data["type"]),
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    files=msg_data.get("files", []),
                    metadata=msg_data.get("metadata", {})
                )
                messages.append(message)
            
            # Convert context
            context_data = session_data.get("context", {})
            context = ConversationContext(
                session_id=context_data["session_id"],
                user_id=context_data.get("user_id"),
                knowledge_level=KnowledgeLevel(context_data.get("knowledge_level", "beginner")),
                user_goals=context_data.get("user_goals", []),
                current_topic=context_data.get("current_topic"),
                previous_calculations=context_data.get("previous_calculations", []),
                client_context=context_data.get("client_context", "personal"),
                needs_external_search=context_data.get("needs_external_search", False),
                calculator_session=context_data.get("calculator_session"),
                calculator_type=CalculatorType(context_data["calculator_type"]) if context_data.get("calculator_type") else None,
                calculator_state=context_data.get("calculator_state"),
                created_at=datetime.fromisoformat(context_data.get("created_at", datetime.utcnow().isoformat())),
                updated_at=datetime.fromisoformat(context_data.get("updated_at", datetime.utcnow().isoformat())),
                follow_up_result=self._dict_to_follow_up_result(context_data.get("follow_up_result")),
                suggested_context_window=context_data.get("suggested_context_window", 1),
                last_follow_up_topics=context_data.get("last_follow_up_topics", [])
            )
            
            # Create session
            session = ChatSession(
                session_id=session_data["session_id"],
                user_id=session_data.get("user_id"),
                messages=messages,
                context=context,
                created_at=datetime.fromisoformat(session_data.get("created_at", datetime.utcnow().isoformat())),
                last_activity=datetime.fromisoformat(session_data.get("last_activity", datetime.utcnow().isoformat())),
                status=session_data.get("status", "active"),
                uploaded_files=session_data.get("uploaded_files", [])
            )
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Error converting dict to session: {e}")
            return None
    
    def _follow_up_result_to_dict(self, follow_up_result) -> Optional[Dict[str, Any]]:
        """Convert FollowUpResult to dictionary"""
        if not follow_up_result:
            return None
        
        try:
            return {
                "is_follow_up": follow_up_result.is_follow_up,
                "related_topics": follow_up_result.related_topics,
                "context_relevance": follow_up_result.context_relevance,
                "suggested_context_window": follow_up_result.suggested_context_window,
                "reasoning": follow_up_result.reasoning,
                "confidence": follow_up_result.confidence,
                "referenced_item": follow_up_result.referenced_item
            }
        except Exception as e:
            logger.error(f"❌ Error converting follow-up result to dict: {e}")
            return None
    
    def _dict_to_follow_up_result(self, follow_up_data) -> Optional[Any]:
        """Convert dictionary to FollowUpResult"""
        if not follow_up_data:
            return None
        
        try:
            from .schemas import FollowUpResult
            return FollowUpResult(
                is_follow_up=follow_up_data.get("is_follow_up", False),
                related_topics=follow_up_data.get("related_topics", []),
                context_relevance=follow_up_data.get("context_relevance", 0.0),
                suggested_context_window=follow_up_data.get("suggested_context_window", 1),
                reasoning=follow_up_data.get("reasoning", ""),
                confidence=follow_up_data.get("confidence", 0.0),
                referenced_item=follow_up_data.get("referenced_item")
            )
        except Exception as e:
            logger.error(f"❌ Error converting dict to follow-up result: {e}")
            return None
    
    async def _get_context_embedding(self, context_text: str) -> List[float]:
        """Get embedding for session context (for searchability)"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=config.openai_api_key)
            
            response = await client.embeddings.create(
                model=config.embedding_model,
                input=context_text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"❌ Error getting context embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about stored sessions"""
        try:
            if self.use_qdrant:
                # Get collection info
                collection_info = self.qdrant_client.get_collection_info(self.collection_name)
                return {
                    "storage_type": "qdrant",
                    "total_sessions": collection_info.vectors_count,
                    "collection_name": self.collection_name
                }
            else:
                return {
                    "storage_type": "memory",
                    "total_sessions": len(self.memory_sessions),
                    "collection_name": "in_memory"
                }
        except Exception as e:
            logger.error(f"❌ Error getting session stats: {e}")
            return {
                "storage_type": "unknown",
                "total_sessions": 0,
                "error": str(e)
            }
