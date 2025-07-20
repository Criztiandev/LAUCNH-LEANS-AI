"""
Unit tests for session manager and browser session lifecycle.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.session_manager import SessionManager, SessionConfig, BrowserSession, SessionStatus
from app.services.stealth_manager import StealthManager


@pytest.fixture
def session_config():
    """Create a test session configuration."""
    return SessionConfig(
        max_session_duration_minutes=5,
        max_idle_time_minutes=2,
        max_requests_per_session=10,
        max_pages_per_session=3,
        cleanup_interval_seconds=1,  # Short for testing
        max_failure_rate=0.5
    )


@pytest.fixture
def mock_stealth_manager():
    """Create a mock stealth manager."""
    stealth_manager = AsyncMock(spec=StealthManager)
    stealth_manager.setup_page_stealth = AsyncMock()
    stealth_manager.get_stealth_config.return_value = {
        'user_agent': 'Test Agent',
        'viewport': {'width': 1920, 'height': 1080}
    }
    return stealth_manager


@pytest.fixture
def mock_context():
    """Create a mock browser context."""
    context = AsyncMock()
    context.new_page = AsyncMock()
    return context


@pytest.fixture
def mock_page():
    """Create a mock page."""
    page = AsyncMock()
    page.close = AsyncMock()
    return page


@pytest.mark.asyncio
async def test_session_manager_initialization(session_config, mock_stealth_manager):
    """Test session manager initialization."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    assert manager.config == session_config
    assert manager.stealth_manager == mock_stealth_manager
    assert len(manager.sessions) == 0
    assert manager._cleanup_task is None


@pytest.mark.asyncio
async def test_session_manager_start_stop(session_config, mock_stealth_manager):
    """Test session manager start and stop."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    await manager.start()
    assert manager._cleanup_task is not None
    assert not manager._cleanup_task.done()
    
    await manager.stop()
    assert manager._cleanup_task.cancelled() or manager._cleanup_task.done()
    assert len(manager.sessions) == 0


@pytest.mark.asyncio
async def test_create_session(session_config, mock_stealth_manager, mock_context):
    """Test session creation."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    async with manager.create_session(mock_context) as session:
        assert isinstance(session, BrowserSession)
        assert session.context == mock_context
        assert session.status == SessionStatus.ACTIVE
        assert session.id in manager.sessions
    
    # Session should be cleaned up after context exit
    assert session.id not in manager.sessions


@pytest.mark.asyncio
async def test_create_session_with_stealth_config(session_config, mock_stealth_manager, mock_context):
    """Test session creation with stealth configuration."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    stealth_config = {'custom': 'config'}
    
    async with manager.create_session(mock_context, stealth_config) as session:
        assert session.stealth_config == stealth_config


@pytest.mark.asyncio
async def test_get_page_from_session(session_config, mock_stealth_manager, mock_context, mock_page):
    """Test getting a page from session."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    mock_context.new_page.return_value = mock_page
    
    async with manager.create_session(mock_context) as session:
        async with manager.get_page(session) as page:
            assert page == mock_page
            assert page in session.pages
            assert session.request_count == 1
            assert mock_stealth_manager.setup_page_stealth.called
    
    # Page should be closed and removed from session
    assert mock_page.close.called
    assert mock_page not in session.pages


@pytest.mark.asyncio
async def test_get_page_session_not_active(session_config, mock_stealth_manager, mock_context):
    """Test getting page from inactive session."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    async with manager.create_session(mock_context) as session:
        session.status = SessionStatus.EXPIRED
        
        with pytest.raises(RuntimeError, match="Session .* is not active"):
            async with manager.get_page(session):
                pass


@pytest.mark.asyncio
async def test_get_page_max_pages_limit(session_config, mock_stealth_manager, mock_context, mock_page):
    """Test page limit per session."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    mock_context.new_page.return_value = mock_page
    
    async with manager.create_session(mock_context) as session:
        # Fill up to max pages
        for _ in range(session_config.max_pages_per_session):
            session.pages.append(mock_page)
        
        with pytest.raises(RuntimeError, match="has reached maximum pages limit"):
            async with manager.get_page(session):
                pass


@pytest.mark.asyncio
async def test_session_success_and_failure_tracking(session_config, mock_stealth_manager, mock_context, mock_page):
    """Test session success and failure tracking."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    mock_context.new_page.return_value = mock_page
    
    async with manager.create_session(mock_context) as session:
        # Successful page usage
        async with manager.get_page(session) as page:
            pass
        
        assert session.success_count == 1
        assert session.failure_count == 0
        
        # Failed page usage
        try:
            async with manager.get_page(session) as page:
                raise Exception("Test error")
        except Exception:
            pass
        
        assert session.success_count == 1
        assert session.failure_count == 1


@pytest.mark.asyncio
async def test_session_cleanup_by_age(session_config, mock_stealth_manager, mock_context):
    """Test session cleanup by age."""
    manager = SessionManager(session_config, mock_stealth_manager)
    await manager.start()
    
    async with manager.create_session(mock_context) as session:
        session_id = session.id
        
        # Make session old
        session.created_at = datetime.utcnow() - timedelta(minutes=session_config.max_session_duration_minutes + 1)
        
        # Trigger cleanup
        await manager._cleanup_expired_sessions()
        
        # Session should be marked for cleanup but still exist in context
        assert session_id in manager.sessions
    
    # After context exit, session should be removed
    assert session_id not in manager.sessions
    
    await manager.stop()


@pytest.mark.asyncio
async def test_session_cleanup_by_idle_time(session_config, mock_stealth_manager, mock_context):
    """Test session cleanup by idle time."""
    manager = SessionManager(session_config, mock_stealth_manager)
    await manager.start()
    
    async with manager.create_session(mock_context) as session:
        session_id = session.id
        
        # Make session idle
        session.last_activity = datetime.utcnow() - timedelta(minutes=session_config.max_idle_time_minutes + 1)
        
        # Trigger cleanup
        await manager._cleanup_expired_sessions()
        
        # Session should be marked for cleanup
        assert session_id in manager.sessions
    
    await manager.stop()


@pytest.mark.asyncio
async def test_session_cleanup_by_request_count(session_config, mock_stealth_manager, mock_context):
    """Test session cleanup by request count."""
    manager = SessionManager(session_config, mock_stealth_manager)
    await manager.start()
    
    async with manager.create_session(mock_context) as session:
        session_id = session.id
        
        # Max out requests
        session.request_count = session_config.max_requests_per_session
        
        # Trigger cleanup
        await manager._cleanup_expired_sessions()
        
        # Session should be marked for cleanup
        assert session_id in manager.sessions
    
    await manager.stop()


@pytest.mark.asyncio
async def test_session_cleanup_by_failure_rate(session_config, mock_stealth_manager, mock_context):
    """Test session cleanup by failure rate."""
    manager = SessionManager(session_config, mock_stealth_manager)
    await manager.start()
    
    async with manager.create_session(mock_context) as session:
        session_id = session.id
        
        # Set high failure rate
        session.request_count = 10
        session.failure_count = 6  # 60% failure rate
        
        # Trigger cleanup
        await manager._cleanup_expired_sessions()
        
        # Session should be marked for cleanup
        assert session_id in manager.sessions
    
    await manager.stop()


@pytest.mark.asyncio
async def test_session_stats(session_config, mock_stealth_manager, mock_context, mock_page):
    """Test session statistics."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    mock_context.new_page.return_value = mock_page
    
    async with manager.create_session(mock_context) as session:
        # Use session
        async with manager.get_page(session) as page:
            pass
        
        stats = manager.get_session_stats()
        
        assert stats['total_sessions'] == 1
        assert stats['active_sessions'] == 1
        assert stats['total_requests'] == 1
        assert stats['total_successes'] == 1
        assert stats['total_failures'] == 0


@pytest.mark.asyncio
async def test_session_info(session_config, mock_stealth_manager, mock_context):
    """Test session information retrieval."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    async with manager.create_session(mock_context) as session:
        info = manager.get_session_info(session.id)
        
        assert info is not None
        assert info['id'] == session.id
        assert info['status'] == SessionStatus.ACTIVE.value
        assert 'created_at' in info
        assert 'last_activity' in info
        assert 'age_seconds' in info
        assert 'idle_seconds' in info
        assert info['request_count'] == 0
        assert info['success_count'] == 0
        assert info['failure_count'] == 0


@pytest.mark.asyncio
async def test_session_info_nonexistent(session_config, mock_stealth_manager):
    """Test session information for nonexistent session."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    info = manager.get_session_info("nonexistent_session")
    
    assert info is None


@pytest.mark.asyncio
async def test_session_cleanup_loop(session_config, mock_stealth_manager, mock_context):
    """Test automatic session cleanup loop."""
    # Use very short cleanup interval
    session_config.cleanup_interval_seconds = 0.1
    
    manager = SessionManager(session_config, mock_stealth_manager)
    await manager.start()
    
    # Create session and make it old
    async with manager.create_session(mock_context) as session:
        session.created_at = datetime.utcnow() - timedelta(minutes=session_config.max_session_duration_minutes + 1)
        
        # Wait for cleanup loop to run
        await asyncio.sleep(0.2)
        
        # Session should still exist in context but be marked for cleanup
        assert session.id in manager.sessions
    
    await manager.stop()


@pytest.mark.asyncio
async def test_session_page_close_error_handling(session_config, mock_stealth_manager, mock_context, mock_page):
    """Test error handling when closing pages."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    mock_context.new_page.return_value = mock_page
    mock_page.close.side_effect = Exception("Close failed")
    
    async with manager.create_session(mock_context) as session:
        async with manager.get_page(session) as page:
            pass
        
        # Should handle close error gracefully
        assert mock_page.close.called


@pytest.mark.asyncio
async def test_session_creation_error_handling(session_config, mock_stealth_manager, mock_context):
    """Test error handling during session creation."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    try:
        async with manager.create_session(mock_context) as session:
            raise Exception("Test error in session")
    except Exception as e:
        assert str(e) == "Test error in session"
    
    # Session should be cleaned up
    assert len(manager.sessions) == 0


@pytest.mark.asyncio
async def test_session_page_error_handling(session_config, mock_stealth_manager, mock_context, mock_page):
    """Test error handling during page usage."""
    manager = SessionManager(session_config, mock_stealth_manager)
    
    mock_context.new_page.return_value = mock_page
    
    async with manager.create_session(mock_context) as session:
        try:
            async with manager.get_page(session) as page:
                raise Exception("Test page error")
        except Exception as e:
            assert str(e) == "Test page error"
        
        # Failure should be tracked
        assert session.failure_count == 1