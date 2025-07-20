"""Test configuration and fixtures."""

import pytest
from unittest.mock import Mock, AsyncMock
from app.services.supabase_service import SupabaseService


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = Mock()
    mock_table = Mock()
    mock_client.table.return_value = mock_table
    return mock_client, mock_table


@pytest.fixture
def supabase_service_with_mock(mock_supabase_client):
    """SupabaseService instance with mocked client."""
    mock_client, mock_table = mock_supabase_client
    service = SupabaseService()
    service.client = mock_client
    return service, mock_table


@pytest.fixture
def sample_validation_data():
    """Sample validation data for testing."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "user123",
        "title": "Test SaaS Idea",
        "idea_text": "A revolutionary SaaS platform for testing",
        "status": "processing",
        "market_score": None,
        "competitor_count": 0,
        "feedback_count": 0
    }


@pytest.fixture
def sample_competitor_data():
    """Sample competitor data for testing."""
    return {
        "id": "comp123",
        "validation_id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Competitor",
        "description": "A competing product",
        "website": "https://competitor.com",
        "estimated_users": 1000,
        "estimated_revenue": "$10k/month",
        "pricing_model": "Subscription",
        "source": "Product Hunt",
        "confidence_score": 0.85
    }