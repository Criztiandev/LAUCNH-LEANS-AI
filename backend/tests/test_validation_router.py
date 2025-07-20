"""Tests for validation processing router."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import BackgroundTasks

from app.main import app
from app.routers.validation import (
    process_validation_background, 
    calculate_market_score,
    ProcessValidationRequest
)
from app.scrapers.base_scraper import CompetitorData, FeedbackData


class TestValidationRouter:
    """Test cases for validation processing router."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_process_validation_endpoint_success(self):
        """Test successful validation processing request."""
        with patch('app.routers.validation.supabase_service') as mock_supabase:
            # Mock validation exists and is in correct state
            mock_supabase.get_validation = AsyncMock(return_value={
                'id': 'test-validation-id',
                'status': 'created',
                'idea_text': 'Test SaaS idea'
            })
            
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": "test-validation-id"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Validation processing started"
            assert data["validation_id"] == "test-validation-id"
            assert data["status"] == "processing"
    
    def test_process_validation_not_found(self):
        """Test validation processing when validation doesn't exist."""
        with patch('app.routers.validation.supabase_service') as mock_supabase:
            mock_supabase.get_validation = AsyncMock(return_value=None)
            
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": "nonexistent-id"}
            )
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    def test_process_validation_already_completed(self):
        """Test validation processing when validation is already completed."""
        with patch('app.routers.validation.supabase_service') as mock_supabase:
            mock_supabase.get_validation = AsyncMock(return_value={
                'id': 'test-validation-id',
                'status': 'completed',
                'idea_text': 'Test SaaS idea'
            })
            
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": "test-validation-id"}
            )
            
            assert response.status_code == 400
            assert "already completed" in response.json()["detail"]
    
    def test_process_validation_already_processing(self):
        """Test validation processing when validation is already being processed."""
        with patch('app.routers.validation.supabase_service') as mock_supabase:
            mock_supabase.get_validation = AsyncMock(return_value={
                'id': 'test-validation-id',
                'status': 'processing',
                'idea_text': 'Test SaaS idea'
            })
            
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": "test-validation-id"}
            )
            
            assert response.status_code == 400
            assert "already being processed" in response.json()["detail"]
    
    def test_process_validation_invalid_request(self):
        """Test validation processing with invalid request data."""
        response = self.client.post(
            "/api/process-validation",
            json={"invalid_field": "test"}
        )
        
        assert response.status_code == 422  # Validation error


class TestBackgroundProcessing:
    """Test cases for background validation processing."""
    
    @pytest.mark.asyncio
    async def test_process_validation_background_success(self):
        """Test successful background validation processing."""
        validation_id = "test-validation-id"
        
        # Mock validation data
        mock_validation = {
            'id': validation_id,
            'idea_text': 'AI-powered project management tool for remote teams',
            'status': 'created'
        }
        
        # Mock competitor data
        mock_competitors = [
            CompetitorData(
                name="Asana",
                description="Team collaboration platform",
                website="https://asana.com",
                estimated_users=100000,
                estimated_revenue="$100M+ ARR",
                pricing_model="Subscription",
                source="Product Hunt",
                source_url="https://producthunt.com/posts/asana",
                confidence_score=0.9
            ),
            CompetitorData(
                name="Trello",
                description="Visual project management",
                website="https://trello.com",
                estimated_users=50000,
                estimated_revenue="$50M+ ARR",
                pricing_model="Freemium",
                source="Product Hunt",
                source_url="https://producthunt.com/posts/trello",
                confidence_score=0.8
            )
        ]
        
        # Mock feedback data
        mock_feedback = [
            FeedbackData(
                text="Great tool for team collaboration",
                sentiment="positive",
                sentiment_score=0.8,
                source="Product Hunt",
                source_url="https://producthunt.com/posts/asana",
                author_info={"username": "user1"}
            )
        ]
        
        # Mock scraping results
        mock_scraping_results = {
            'competitors': mock_competitors,
            'feedback': mock_feedback,
            'metadata': {
                'validation_id': validation_id,
                'processing_time_seconds': 45.2,
                'sources_attempted': 1,
                'sources_successful': 1,
                'sources_partial': 0,
                'sources_failed': 0,
                'successful_sources': ['Product Hunt'],
                'partial_sources': [],
                'failed_sources': [],
                'total_competitors_found': 2,
                'total_feedback_found': 1
            }
        }
        
        with patch('app.routers.validation.supabase_service') as mock_supabase, \
             patch('app.routers.validation.ScrapingService') as mock_scraping_service_class:
            
            # Setup supabase mocks
            mock_supabase.get_validation = AsyncMock(return_value=mock_validation)
            mock_supabase.update_validation_status = AsyncMock(return_value=True)
            mock_supabase.create_competitor = AsyncMock(return_value="competitor-id")
            mock_supabase.create_feedback = AsyncMock(return_value="feedback-id")
            mock_supabase.update_validation_counts = AsyncMock(return_value=True)
            
            # Setup scraping service mock
            mock_scraping_service = MagicMock()
            mock_scraping_service.register_scraper = MagicMock(return_value=None)
            mock_scraping_service.get_registered_scrapers = MagicMock(return_value=['Product Hunt'])
            mock_scraping_service.scrape_all_sources = AsyncMock(return_value=mock_scraping_results)
            mock_scraping_service_class.return_value = mock_scraping_service
            
            # Run background processing
            await process_validation_background(validation_id)
            
            # Verify supabase calls
            assert mock_supabase.update_validation_status.call_count >= 2
            
            # Check that the first call was to set status to processing
            first_call_args = mock_supabase.update_validation_status.call_args_list[0]
            assert first_call_args[0][0] == validation_id
            assert first_call_args[0][1] == "processing"
            assert "processing_started_at" in first_call_args[1]
            
            # Check that the last call was to set status to completed
            last_call_args = mock_supabase.update_validation_status.call_args_list[-1]
            assert last_call_args[0][0] == validation_id
            assert last_call_args[0][1] == "completed"
            assert "market_score" in last_call_args[1]
            assert "completed_at" in last_call_args[1]
            assert "sources_scraped" in last_call_args[1]
            
            # Verify competitor creation
            assert mock_supabase.create_competitor.call_count == 2
            
            # Verify feedback creation
            assert mock_supabase.create_feedback.call_count == 1
            
            # Verify counts update
            assert mock_supabase.update_validation_counts.call_count == 1
    
    @pytest.mark.asyncio
    async def test_process_validation_background_validation_not_found(self):
        """Test background processing when validation is not found."""
        validation_id = "nonexistent-validation-id"
        
        with patch('app.routers.validation.supabase_service') as mock_supabase:
            mock_supabase.get_validation = AsyncMock(return_value=None)
            mock_supabase.update_validation_status = AsyncMock(return_value=True)
            
            await process_validation_background(validation_id)
            
            # Should update status to failed
            assert mock_supabase.update_validation_status.call_count >= 2
            
            # Check that the last call was to set status to failed
            last_call_args = mock_supabase.update_validation_status.call_args_list[-1]
            assert last_call_args[0][0] == validation_id
            assert last_call_args[0][1] == "failed"
            assert "error_message" in last_call_args[1]
            assert "Validation not found" in last_call_args[1]["error_message"]
    
    @pytest.mark.asyncio
    async def test_process_validation_background_no_idea_text(self):
        """Test background processing when validation has no idea text."""
        validation_id = "test-validation-id"
        
        mock_validation = {
            'id': validation_id,
            'idea_text': '',  # Empty idea text
            'status': 'created'
        }
        
        with patch('app.routers.validation.supabase_service') as mock_supabase:
            mock_supabase.get_validation = AsyncMock(return_value=mock_validation)
            mock_supabase.update_validation_status = AsyncMock(return_value=True)
            
            await process_validation_background(validation_id)
            
            # Should update status to failed
            assert mock_supabase.update_validation_status.call_count >= 2
            
            # Check that the last call was to set status to failed
            last_call_args = mock_supabase.update_validation_status.call_args_list[-1]
            assert last_call_args[0][0] == validation_id
            assert last_call_args[0][1] == "failed"
            assert "error_message" in last_call_args[1]
            assert "No idea text provided" in last_call_args[1]["error_message"]
    
    @pytest.mark.asyncio
    async def test_process_validation_background_scraping_error(self):
        """Test background processing when scraping fails."""
        validation_id = "test-validation-id"
        
        mock_validation = {
            'id': validation_id,
            'idea_text': 'Test SaaS idea',
            'status': 'created'
        }
        
        with patch('app.routers.validation.supabase_service') as mock_supabase, \
             patch('app.routers.validation.ScrapingService') as mock_scraping_service_class:
            
            mock_supabase.get_validation = AsyncMock(return_value=mock_validation)
            mock_supabase.update_validation_status = AsyncMock(return_value=True)
            
            # Setup scraping service to raise exception
            mock_scraping_service = MagicMock()
            mock_scraping_service.register_scraper = MagicMock(return_value=None)
            mock_scraping_service.get_registered_scrapers = MagicMock(return_value=['Product Hunt'])
            mock_scraping_service.scrape_all_sources = AsyncMock(side_effect=Exception("Scraping failed"))
            mock_scraping_service_class.return_value = mock_scraping_service
            
            await process_validation_background(validation_id)
            
            # Should update status to failed
            assert mock_supabase.update_validation_status.call_count >= 2
            
            # Check that the last call was to set status to failed
            last_call_args = mock_supabase.update_validation_status.call_args_list[-1]
            assert last_call_args[0][0] == validation_id
            assert last_call_args[0][1] == "failed"
            assert "error_message" in last_call_args[1]
            assert "Scraping failed" in last_call_args[1]["error_message"]
            assert "failed_at" in last_call_args[1]


class TestMarketScoreCalculation:
    """Test cases for market score calculation."""
    
    def test_calculate_market_score_no_competition(self):
        """Test market score calculation with no competition."""
        score = calculate_market_score(
            competitor_count=0,
            feedback_count=10,
            metadata={'sources_attempted': 1, 'sources_successful': 1}
        )
        
        # Base 5.0 + 2.0 (no competition) + 0.5 (good feedback) + 0.5 (high success rate)
        assert score == 8.0
    
    def test_calculate_market_score_high_competition(self):
        """Test market score calculation with high competition."""
        score = calculate_market_score(
            competitor_count=20,
            feedback_count=5,
            metadata={'sources_attempted': 2, 'sources_successful': 1}
        )
        
        # Base 5.0 - 2.0 (very high competition) + 0.0 (some feedback) + 0.0 (moderate success rate)
        assert score == 3.0
    
    def test_calculate_market_score_moderate_scenario(self):
        """Test market score calculation with moderate competition and feedback."""
        score = calculate_market_score(
            competitor_count=5,
            feedback_count=15,
            metadata={'sources_attempted': 3, 'sources_successful': 2}
        )
        
        # Base 5.0 + 0.0 (moderate competition) + 0.5 (good feedback) + 0.0 (moderate success rate)
        assert score == 5.5
    
    def test_calculate_market_score_bounds(self):
        """Test that market score stays within 1.0-10.0 bounds."""
        # Test lower bound
        low_score = calculate_market_score(
            competitor_count=100,
            feedback_count=0,
            metadata={'sources_attempted': 5, 'sources_successful': 0}
        )
        assert low_score >= 1.0
        
        # Test upper bound
        high_score = calculate_market_score(
            competitor_count=0,
            feedback_count=50,
            metadata={'sources_attempted': 1, 'sources_successful': 1}
        )
        assert high_score <= 10.0
    
    def test_calculate_market_score_error_handling(self):
        """Test market score calculation with invalid data."""
        # Should return default score of 5.0 on error
        score = calculate_market_score(
            competitor_count="invalid",  # Invalid type
            feedback_count=10,
            metadata={}
        )
        assert score == 5.0


if __name__ == "__main__":
    pytest.main([__file__])