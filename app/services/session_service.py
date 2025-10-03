"""
Session Management Service for Manna Backend

This service manages user sessions in memory (not database, not Redis).
It provides session creation, validation, and cleanup functionality.
"""

import time
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
import threading


@dataclass
class UserSession:
    """User session data structure"""
    session_id: str
    user_id: int
    user_type: str  # 'church_admin', 'platform_admin', 'donor', 'mobile_user'
    church_id: Optional[int] = None
    device_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    is_active: bool = True
    access_token_jti: Optional[str] = None
    refresh_token: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_activity is None:
            self.last_activity = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return asdict(self)

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)

    def is_expired(self, max_idle_minutes: int = 30) -> bool:
        """Check if session is expired due to inactivity"""
        if not self.is_active or self.last_activity is None:
            return True
        
        idle_time = datetime.now(timezone.utc) - self.last_activity
        return idle_time.total_seconds() > (max_idle_minutes * 60)


class SessionManager:
    """In-memory session manager for user sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}
        self._user_sessions: Dict[int, List[str]] = {}  # user_id -> [session_ids]
        self._lock = threading.RLock()
        self._cleanup_interval = 300  # 5 minutes
        self._max_idle_minutes = 30
        self._max_sessions_per_user = 5
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self._cleanup_interval)
                    self.cleanup_expired_sessions()
                except Exception as e:
                    pass
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        pass
    
    def create_session(
        self,
        user_id: int,
        user_type: str,
        church_id: Optional[int] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        access_token_jti: Optional[str] = None,
        refresh_token: Optional[str] = None
    ) -> str:
        """Create a new user session"""
        with self._lock:
            # Check if user has too many active sessions
            user_session_ids = self._user_sessions.get(user_id, [])
            active_sessions = []
            
            for sid in user_session_ids:
                session = self._sessions.get(sid)
                if session and session.is_active and not session.is_expired(self._max_idle_minutes):
                    active_sessions.append(sid)
            
            if len(active_sessions) >= self._max_sessions_per_user:
                # Remove oldest session
                oldest_session_id = min(active_sessions, key=lambda sid: self._sessions[sid].created_at or datetime.now(timezone.utc))
                self._remove_session(oldest_session_id)
            
            # Generate unique session ID
            session_id = f"sess_{user_id}_{int(time.time())}_{hash(f'{ip_address}{user_agent}')}"
            
            # Create session
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                user_type=user_type,
                church_id=church_id,
                device_info=device_info,
                ip_address=ip_address,
                user_agent=user_agent,
                access_token_jti=access_token_jti,
                refresh_token=refresh_token
            )
            
            # Store session
            self._sessions[session_id] = session
            
            # Update user sessions mapping
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(session_id)
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = self._sessions.get(session_id)
        if session and session.is_active and not session.is_expired(self._max_idle_minutes):
            session.update_activity()
            return session
        return None
    
    def get_user_sessions(self, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user"""
        with self._lock:
            user_session_ids = self._user_sessions.get(user_id, [])
            active_sessions = []
            
            for session_id in user_session_ids:
                session = self._sessions.get(session_id)
                if session and session.is_active and not session.is_expired(self._max_idle_minutes):
                    active_sessions.append(session)
                elif session and (not session.is_active or session.is_expired(self._max_idle_minutes)):
                    # Clean up expired/inactive sessions
                    self._remove_session(session_id)
            
            return active_sessions
    
    def validate_session(self, session_id: str, user_id: int) -> bool:
        """Validate if session exists and belongs to user"""
        session = self.get_session(session_id)
        return session is not None and session.user_id == user_id
    
    def update_session_activity(self, session_id: str):
        """Update session last activity"""
        session = self._sessions.get(session_id)
        if session:
            session.update_activity()
    
    def deactivate_session(self, session_id: str):
        """Deactivate a session (soft delete)"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.is_active = False
    
    def remove_session(self, session_id: str):
        """Remove a session completely"""
        with self._lock:
            self._remove_session(session_id)
    
    def _remove_session(self, session_id: str):
        """Internal method to remove session"""
        session = self._sessions.get(session_id)
        if session:
            # Remove from user sessions mapping
            user_session_ids = self._user_sessions.get(session.user_id, [])
            if session_id in user_session_ids:
                user_session_ids.remove(session_id)
            
            # Remove session
            del self._sessions[session_id]
    
    def logout_user(self, user_id: int, session_id: Optional[str] = None):
        """Logout user from specific session or all sessions"""
        with self._lock:
            if session_id:
                # Logout from specific session
                self.deactivate_session(session_id)
            else:
                # Logout from all sessions
                user_session_ids = self._user_sessions.get(user_id, [])
                for sid in user_session_ids:
                    self.deactivate_session(sid)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        with self._lock:
            expired_sessions = []
            current_time = datetime.now(timezone.utc)
            
            for session_id, session in self._sessions.items():
                if session.is_expired(self._max_idle_minutes):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self._remove_session(session_id)
            
            if expired_sessions:
                pass
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        with self._lock:
            total_sessions = len(self._sessions)
            active_sessions = sum(1 for s in self._sessions.values() if s.is_active)
            total_users = len(self._user_sessions)
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_users": total_users,
                "cleanup_interval": self._cleanup_interval,
                "max_idle_minutes": self._max_idle_minutes
            }
    
    def find_session_by_token_jti(self, jti: str) -> Optional[UserSession]:
        """Find session by access token JTI"""
        for session in self._sessions.values():
            if session.access_token_jti == jti and session.is_active:
                return session
        return None
    
    def find_session_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """Find session by refresh token"""
        for session in self._sessions.values():
            if session.refresh_token == refresh_token and session.is_active:
                return session
        return None


# Global session manager instance
session_manager = SessionManager()
