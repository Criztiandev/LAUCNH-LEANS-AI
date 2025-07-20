"""
Session manager for browser session lifecycle and resource cleanup.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

from patchright.async_api import BrowserContext, Page

from .stealth_manager import StealthManager, StealthConfig


logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Status of browser session."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class BrowserSession:
    """Represents a browser session."""
    id: str
    context: BrowserContext
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    pages: List[Page] = field(default_factory=list)
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    stealth_config: Optional[Dict[str, Any]] = None


@dataclass
class SessionConfig:
    """Configuration for session management."""
    max_session_duration_minutes: int = 15
    max_idle_time_minutes: int = 5
    max_requests_per_session: int = 20
    max_pages_per_session: int = 5
    cleanup_interval_seconds: int = 60
    max_failure_rate: float = 0.5


class SessionManager:
    """Manages browser session lifecycle and resource cleanup."""
    
    def __init__(self, config: Optional[SessionConfig] = None, stealth_manager: Optional[StealthManager] = None):
        """Initialize the session manager."""
        self.config = config or SessionConfig()
        self.stealth_manager = stealth_manager or StealthManager()
        self.sessions: Dict[str, BrowserSession] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        self._session_counter = 0
    
    async def start(self) -> None:
        """Start the session manager."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Session manager started")
    
    async def stop(self) -> None:
        """Stop the session manager and cleanup all sessions."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all sessions
        async with self._lock:
            for session in list(self.sessions.values()):
                await self._close_session(session.id)
        
        logger.info("Session manager stopped")
    
    @asynccontextmanager
    async def create_session(self, context: BrowserContext, stealth_config: Optional[Dict[str, Any]] = None):
        """
        Create a managed browser session.
        
        Args:
            context: Browser context to manage
            stealth_config: Optional stealth configuration
            
        Yields:
            BrowserSession: A managed browser session
        """
        session = await self._create_session(context, stealth_config)
        
        try:
            yield session
        except Exception as e:
            logger.error(f"Error in session {session.id}: {str(e)}")
            session.failure_count += 1
            session.status = SessionStatus.FAILED
            raise
        finally:
            await self._close_session(session.id)
    
    @asynccontextmanager
    async def get_page(self, session: BrowserSession):
        """
        Get a page from the session with stealth setup.
        
        Args:
            session: Browser session to get page from
            
        Yields:
            Page: A page ready for use
        """
        if session.status != SessionStatus.ACTIVE:
            raise RuntimeError(f"Session {session.id} is not active")
        
        if len(session.pages) >= self.config.max_pages_per_session:
            raise RuntimeError(f"Session {session.id} has reached maximum pages limit")
        
        page = None
        try:
            page = await session.context.new_page()
            session.pages.append(page)
            
            # Setup stealth measures
            await self.stealth_manager.setup_page_stealth(page)
            
            # Update session activity
            session.last_activity = datetime.utcnow()
            session.request_count += 1
            
            yield page
            
            session.success_count += 1
            
        except Exception as e:
            logger.error(f"Error with page in session {session.id}: {str(e)}")
            session.failure_count += 1
            raise
        finally:
            if page:
                try:
                    await page.close()
                    if page in session.pages:
                        session.pages.remove(page)
                except Exception as e:
                    logger.warning(f"Error closing page: {str(e)}")
    
    async def _create_session(self, context: BrowserContext, stealth_config: Optional[Dict[str, Any]] = None) -> BrowserSession:
        """Create a new browser session."""
        async with self._lock:
            self._session_counter += 1
            session_id = f"session_{self._session_counter}_{int(datetime.utcnow().timestamp())}"
            
            session = BrowserSession(
                id=session_id,
                context=context,
                stealth_config=stealth_config or self.stealth_manager.get_stealth_config()
            )
            
            self.sessions[session_id] = session
            logger.info(f"Created session: {session_id}")
            
            return session
    
    async def _close_session(self, session_id: str) -> None:
        """Close and cleanup a session."""
        async with self._lock:
            if session_id not in self.sessions:
                return
            
            session = self.sessions[session_id]
            
            try:
                # Close all pages
                for page in list(session.pages):
                    try:
                        await page.close()
                    except Exception as e:
                        logger.warning(f"Error closing page: {str(e)}")
                
                session.pages.clear()
                session.status = SessionStatus.EXPIRED
                
                logger.info(f"Closed session: {session_id} (requests: {session.request_count}, success: {session.success_count}, failures: {session.failure_count})")
                
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {str(e)}")
            finally:
                del self.sessions[session_id]
    
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {str(e)}")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired or failed sessions."""
        current_time = datetime.utcnow()
        sessions_to_close = []
        
        async with self._lock:
            for session_id, session in self.sessions.items():
                should_close = False
                
                # Check session duration
                session_age = current_time - session.created_at
                if session_age > timedelta(minutes=self.config.max_session_duration_minutes):
                    logger.info(f"Session {session_id} expired due to age: {session_age}")
                    should_close = True
                
                # Check idle time
                idle_time = current_time - session.last_activity
                if idle_time > timedelta(minutes=self.config.max_idle_time_minutes):
                    logger.info(f"Session {session_id} expired due to idle time: {idle_time}")
                    should_close = True
                
                # Check request count
                if session.request_count >= self.config.max_requests_per_session:
                    logger.info(f"Session {session_id} expired due to request count: {session.request_count}")
                    should_close = True
                
                # Check failure rate
                if session.request_count > 0:
                    failure_rate = session.failure_count / session.request_count
                    if failure_rate > self.config.max_failure_rate:
                        logger.info(f"Session {session_id} expired due to failure rate: {failure_rate}")
                        should_close = True
                
                # Check status
                if session.status in [SessionStatus.FAILED, SessionStatus.EXPIRED]:
                    should_close = True
                
                if should_close:
                    sessions_to_close.append(session_id)
        
        # Close expired sessions
        for session_id in sessions_to_close:
            await self._close_session(session_id)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        stats = {
            'total_sessions': len(self.sessions),
            'active_sessions': 0,
            'idle_sessions': 0,
            'failed_sessions': 0,
            'total_requests': 0,
            'total_successes': 0,
            'total_failures': 0,
            'total_pages': 0,
        }
        
        for session in self.sessions.values():
            stats['total_requests'] += session.request_count
            stats['total_successes'] += session.success_count
            stats['total_failures'] += session.failure_count
            stats['total_pages'] += len(session.pages)
            
            if session.status == SessionStatus.ACTIVE:
                stats['active_sessions'] += 1
            elif session.status == SessionStatus.IDLE:
                stats['idle_sessions'] += 1
            elif session.status == SessionStatus.FAILED:
                stats['failed_sessions'] += 1
        
        return stats
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        current_time = datetime.utcnow()
        
        return {
            'id': session.id,
            'status': session.status.value,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'age_seconds': (current_time - session.created_at).total_seconds(),
            'idle_seconds': (current_time - session.last_activity).total_seconds(),
            'request_count': session.request_count,
            'success_count': session.success_count,
            'failure_count': session.failure_count,
            'active_pages': len(session.pages),
            'stealth_config': session.stealth_config,
        }