"""Tests for SupabaseService."""

import pytest
from unittest.mock import Mock, patch
from app.services.supabase_service import SupabaseService


class TestSupabaseService:
    """Test cases for SupabaseService."""
    
    @pytest.mark.asyncio
    async def test_update_validation_status_success(self, supabase_service_with_mock, sample_validation_data):
        """Test successful validation status update."""
        service, mock_table = supabase_service_with_mock
        
        # Mock successful update
        mock_execute = Mock()
        mock_execute.data = [sample_validation_data]
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_execute
        
        result = await service.update_validation_status("test-id", "completed", market_score=8.5)
        
        assert result is True
        mock_table.update.assert_called_once_with({"status": "completed", "market_score": 8.5})
        mock_table.update.return_value.eq.assert_called_once_with("id", "test-id")
    
    @pytest.mark.asyncio
    async def test_update_validation_status_failure(self, supabase_service_with_mock):
        """Test validation status update failure."""
        service, mock_table = supabase_service_with_mock
        
        # Mock failed update (no data returned)
        mock_execute = Mock()
        mock_execute.data = []
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_execute
        
        result = await service.update_validation_status("test-id", "failed")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_validation_status_exception(self, supabase_service_with_mock):
        """Test validation status update with exception."""
        service, mock_table = supabase_service_with_mock
        
        # Mock exception
        mock_table.update.side_effect = Exception("Database error")
        
        result = await service.update_validation_status("test-id", "completed")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_validation_success(self, supabase_service_with_mock, sample_validation_data):
        """Test successful validation retrieval."""
        service, mock_table = supabase_service_with_mock
        
        # Mock successful query
        mock_execute = Mock()
        mock_execute.data = [sample_validation_data]
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_execute
        
        result = await service.get_validation("test-id")
        
        assert result == sample_validation_data
        mock_table.select.assert_called_once_with("*")
        mock_table.select.return_value.eq.assert_called_once_with("id", "test-id")
    
    @pytest.mark.asyncio
    async def test_get_validation_not_found(self, supabase_service_with_mock):
        """Test validation retrieval when not found."""
        service, mock_table = supabase_service_with_mock
        
        # Mock empty result
        mock_execute = Mock()
        mock_execute.data = []
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_execute
        
        result = await service.get_validation("nonexistent-id")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_competitor_success(self, supabase_service_with_mock, sample_competitor_data):
        """Test successful competitor creation."""
        service, mock_table = supabase_service_with_mock
        
        # Mock successful insert
        mock_execute = Mock()
        mock_execute.data = [sample_competitor_data]
        mock_table.insert.return_value.execute.return_value = mock_execute
        
        result = await service.create_competitor(
            validation_id="test-validation-id",
            name="Test Competitor",
            description="A test competitor",
            source="Product Hunt",
            confidence_score=0.85
        )
        
        assert result == sample_competitor_data["id"]
        mock_table.insert.assert_called_once()
        
        # Verify the data passed to insert
        insert_data = mock_table.insert.call_args[0][0]
        assert insert_data["validation_id"] == "test-validation-id"
        assert insert_data["name"] == "Test Competitor"
        assert insert_data["description"] == "A test competitor"
        assert insert_data["source"] == "Product Hunt"
        assert insert_data["confidence_score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_create_feedback_success(self, supabase_service_with_mock):
        """Test successful feedback creation."""
        service, mock_table = supabase_service_with_mock
        
        # Mock successful insert
        feedback_data = {"id": "feedback123"}
        mock_execute = Mock()
        mock_execute.data = [feedback_data]
        mock_table.insert.return_value.execute.return_value = mock_execute
        
        result = await service.create_feedback(
            validation_id="test-validation-id",
            text="Great product idea!",
            sentiment="positive",
            sentiment_score=0.9,
            source="Reddit"
        )
        
        assert result == "feedback123"
        mock_table.insert.assert_called_once()
        
        # Verify the data passed to insert
        insert_data = mock_table.insert.call_args[0][0]
        assert insert_data["validation_id"] == "test-validation-id"
        assert insert_data["text"] == "Great product idea!"
        assert insert_data["sentiment"] == "positive"
        assert insert_data["sentiment_score"] == 0.9
        assert insert_data["source"] == "Reddit"
    
    @pytest.mark.asyncio
    async def test_update_validation_counts_success(self, supabase_service_with_mock):
        """Test successful validation counts update."""
        service, mock_table = supabase_service_with_mock
        
        # Mock count queries
        competitor_result = Mock()
        competitor_result.count = 5
        feedback_result = Mock()
        feedback_result.count = 10
        update_result = Mock()
        update_result.data = [{"id": "test-id"}]
        
        mock_table.select.return_value.eq.return_value.execute.side_effect = [
            competitor_result,  # First call for competitors
            feedback_result,    # Second call for feedback
        ]
        mock_table.update.return_value.eq.return_value.execute.return_value = update_result
        
        result = await service.update_validation_counts("test-validation-id")
        
        assert result is True
        
        # Verify update was called with correct counts
        mock_table.update.assert_called_once_with({
            "competitor_count": 5,
            "feedback_count": 10
        })
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, supabase_service_with_mock):
        """Test successful health check."""
        service, mock_table = supabase_service_with_mock
        
        # Mock successful query
        mock_execute = Mock()
        mock_execute.data = []
        mock_table.select.return_value.limit.return_value.execute.return_value = mock_execute
        
        result = await service.health_check()
        
        assert result is True
        mock_table.select.assert_called_once_with("id")
        mock_table.select.return_value.limit.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, supabase_service_with_mock):
        """Test health check failure."""
        service, mock_table = supabase_service_with_mock
        
        # Mock exception
        mock_table.select.side_effect = Exception("Connection failed")
        
        result = await service.health_check()
        
        assert result is False