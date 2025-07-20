"""
End-to-end test for validation processing with Product Hunt scraper.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json
import os

from app.main import app
from app.scrapers.base_scraper import ScrapingStatus, CompetitorData, FeedbackData
from app.scrapers.product_hunt_scraper import ProductHuntScraper


class TestValidationProcessingE2E:
    """End-to-end test for validation processing with Product Hunt scraper."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_validation_processing_e2e_with_product_hunt(self):
        """Test end-to-end validation processing with Product Hunt scraper."""
        validation_id = "test-validation-id"
        idea_text = "AI-powered project management tool for remote teams"
        
        # Mock validation data
        mock_validation = {
            'id': validation_id,
            'idea_text': idea_text,
            'status': 'created'
        }
        
        # Mock competitor data that would be extracted from Product Hunt
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
        
        # Create mock scraping result
        mock_result = MagicMock()
        mock_result.status = ScrapingStatus.SUCCESS
        mock_result.competitors = mock_competitors
        mock_result.feedback = mock_feedback
        mock_result.metadata = {
            'keywords_searched': ['AI', 'project', 'management'],
            'total_found': len(mock_competitors),
            'source': 'Product Hunt'
        }
        
        with patch('app.routers.validation.supabase_service') as mock_supabase, \
             patch('app.scrapers.product_hunt_scraper.ProductHuntScraper.scrape') as mock_scrape:
            
            # Setup supabase mocks
            mock_supabase.get_validation = AsyncMock(return_value=mock_validation)
            mock_supabase.update_validation_status = AsyncMock(return_value=True)
            mock_supabase.create_competitor = AsyncMock(return_value="competitor-id")
            mock_supabase.create_feedback = AsyncMock(return_value="feedback-id")
            mock_supabase.update_validation_counts = AsyncMock(return_value=True)
            
            # Setup scraper mock to return our test data
            mock_scrape.return_value = mock_result
            
            # Make the API request
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": validation_id}
            )
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Validation processing started"
            assert data["validation_id"] == validation_id
            assert data["status"] == "processing"
            
            # Verify that the validation status was updated to processing
            mock_supabase.update_validation_status.assert_called()
    
    def test_validation_processing_with_real_product_hunt_scraper(self):
        """Test validation processing with a real ProductHuntScraper instance."""
        validation_id = "test-validation-id"
        idea_text = "AI-powered project management tool for remote teams"
        
        # Mock validation data
        mock_validation = {
            'id': validation_id,
            'idea_text': idea_text,
            'status': 'created'
        }
        
        # Create a real ProductHuntScraper instance but mock its HTTP requests
        with patch('app.routers.validation.supabase_service') as mock_supabase, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Setup supabase mocks
            mock_supabase.get_validation = AsyncMock(return_value=mock_validation)
            mock_supabase.update_validation_status = AsyncMock(return_value=True)
            mock_supabase.create_competitor = AsyncMock(return_value="competitor-id")
            mock_supabase.create_feedback = AsyncMock(return_value="feedback-id")
            mock_supabase.update_validation_counts = AsyncMock(return_value=True)
            
            # Setup mock HTTP response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            # Load mock HTML response from file if it exists, otherwise use a simple mock
            mock_html_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'product_hunt_search.html')
            if os.path.exists(mock_html_path):
                with open(mock_html_path, 'r', encoding='utf-8') as f:
                    mock_response.text = AsyncMock(return_value=f.read())
            else:
                # Simple mock HTML with product data
                mock_response.text = AsyncMock(return_value="""
                <html>
                <body>
                    <div class="styles_item__Dk_nz">
                        <a class="styles_title__HzPeb" href="/posts/asana">Asana</a>
                        <div class="color-lighter-grey fontSize-mobile-12 fontSize-desktop-16 fontSize-tablet-16 fontSize-widescreen-16 fontWeight-400 noOfLines-2">
                            Team collaboration platform
                        </div>
                        <div class="color-lighter-grey fontSize-12 fontWeight-600 noOfLines-undefined">
                            5000 upvotes
                        </div>
                    </div>
                </body>
                </html>
                """)
            
            mock_get.return_value = mock_response
            
            # Make the API request
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": validation_id}
            )
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Validation processing started"
            assert data["validation_id"] == validation_id
            assert data["status"] == "processing"
            
            # Verify that the validation status was updated to processing
            mock_supabase.update_validation_status.assert_called()
    
    def test_validation_processing_error_handling(self):
        """Test error handling in validation processing."""
        validation_id = "test-validation-id"
        
        with patch('app.routers.validation.supabase_service') as mock_supabase:
            # Test case: validation not found
            mock_supabase.get_validation = AsyncMock(return_value=None)
            
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": validation_id}
            )
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
            
            # Test case: validation already completed
            mock_supabase.get_validation = AsyncMock(return_value={
                'id': validation_id,
                'status': 'completed'
            })
            
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": validation_id}
            )
            
            assert response.status_code == 400
            assert "already completed" in response.json()["detail"]
            
            # Test case: validation already processing
            mock_supabase.get_validation = AsyncMock(return_value={
                'id': validation_id,
                'status': 'processing'
            })
            
            response = self.client.post(
                "/api/process-validation",
                json={"validation_id": validation_id}
            )
            
            assert response.status_code == 400
            assert "already being processed" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])