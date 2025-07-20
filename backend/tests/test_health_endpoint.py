"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test cases for health check endpoint."""
    
    @patch('app.routers.health.supabase_service.health_check')
    def test_health_check_success(self, mock_health_check):
        """Test successful health check."""
        # Mock successful health check
        mock_health_check.return_value = AsyncMock(return_value=True)()
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
    
    @patch('app.routers.health.supabase_service.health_check')
    def test_health_check_database_failure(self, mock_health_check):
        """Test health check with database failure."""
        # Mock failed health check
        mock_health_check.return_value = AsyncMock(return_value=False)()
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        assert "Database connection failed" in data["detail"]
    
    @patch('app.routers.health.supabase_service.health_check')
    def test_health_check_exception(self, mock_health_check):
        """Test health check with exception."""
        # Mock exception
        mock_health_check.side_effect = Exception("Unexpected error")
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        assert "Service unhealthy" in data["detail"]