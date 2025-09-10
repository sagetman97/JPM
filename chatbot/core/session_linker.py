"""
Session linking system for managing connections between chat sessions and external tools.
Handles tool session creation, completion tracking, and cleanup.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ToolSession:
    """Represents a tool session linked to a chat session"""
    external_session_id: str
    chat_session_id: str
    tool_type: str  # 'assessment' or 'portfolio'
    status: str  # 'pending', 'completed', 'expired'
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    pdf_id: Optional[str] = None

class SessionLinker:
    """Manages tool sessions and their lifecycle"""
    
    def __init__(self):
        self.pending_sessions: Dict[str, ToolSession] = {}
        self.completed_sessions: Dict[str, ToolSession] = {}
        self.session_ttl_hours = 24
        
    async def create_tool_session(self, chat_session_id: str, tool_type: str) -> str:
        """Create a new tool session linked to a chat session"""
        external_session_id = f"{chat_session_id}_{tool_type}_{uuid.uuid4().hex[:8]}"
        
        tool_session = ToolSession(
            external_session_id=external_session_id,
            chat_session_id=chat_session_id,
            tool_type=tool_type,
            status='pending',
            created_at=datetime.utcnow()
        )
        
        self.pending_sessions[external_session_id] = tool_session
        logger.info(f"🔗 Created tool session: {external_session_id} for chat: {chat_session_id}, type: {tool_type}")
        logger.info(f"🔗 Total pending sessions: {len(self.pending_sessions)}")
        return external_session_id
    
    async def complete_tool_session(self, external_session_id: str, result_data: Dict[str, Any]) -> bool:
        """Mark a tool session as completed with result data"""
        if external_session_id not in self.pending_sessions:
            return False
            
        tool_session = self.pending_sessions[external_session_id]
        tool_session.status = 'completed'
        tool_session.completed_at = datetime.utcnow()
        tool_session.result_data = result_data
        
        # Move to completed sessions
        self.completed_sessions[external_session_id] = tool_session
        del self.pending_sessions[external_session_id]
        
        return True
    
    def get_session_info(self, external_session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        
        # Check pending sessions first
        if external_session_id in self.pending_sessions:
            session = self.pending_sessions[external_session_id]
            return {
                "external_session_id": session.external_session_id,
                "chat_session_id": session.chat_session_id,
                "tool_type": session.tool_type,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            }
        
        # Check completed sessions
        if external_session_id in self.completed_sessions:
            session = self.completed_sessions[external_session_id]
            return {
                "external_session_id": session.external_session_id,
                "chat_session_id": session.chat_session_id,
                "tool_type": session.tool_type,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "has_results": session.result_data is not None
            }
        
        return None
    
    async def get_pending_tools(self, chat_session_id: str) -> List[ToolSession]:
        """Get all pending tools for a chat session"""
        return [session for session in self.pending_sessions.values() 
                if session.chat_session_id == chat_session_id]
    
    async def get_tool_session(self, external_session_id: str) -> Optional[ToolSession]:
        """Get a tool session by external session ID"""
        if external_session_id in self.pending_sessions:
            return self.pending_sessions[external_session_id]
        elif external_session_id in self.completed_sessions:
            return self.completed_sessions[external_session_id]
        return None
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.session_ttl_hours)
        
        expired_sessions = [
            session_id for session_id, session in self.pending_sessions.items()
            if session.created_at < cutoff_time
        ]
        
        for session_id in expired_sessions:
            del self.pending_sessions[session_id]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions"""
        return {
            "pending_sessions": len(self.pending_sessions),
            "completed_sessions": len(self.completed_sessions),
            "total_sessions": len(self.pending_sessions) + len(self.completed_sessions)
        }
