#!/usr/bin/env python3
"""
Test script for Google scraper with mock data to demonstrate functionality.
"""
import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import patch, AsyncMock

from app.scrapers.google_scraper import GoogleScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# Mock HTML response that simulates Google search results
MOCK_GOOGLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>CRM software - Google Search</title></head>
<body>
    <div class="g">
        <h3>Salesforce - #1 CRM Software</h3>
        <a href="https://www.salesforce.com/">
            <div class="VwiC3b">
                Salesforce is the world's #1 CRM platform. Our cloud-based CRM software helps businesses 
                manage customer relationships, sales, and marketing. Try our free trial today.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>HubSpot CRM - Free CRM Software</h3>
        <a href="https://www.hubspot.com/products/crm">
            <div class="VwiC3b">
                HubSpot's free CRM software organizes, tracks, and nurtures your leads and customers. 
                Get started with our powerful, easy-to-use CRM platform.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Pipedrive - Sales CRM for Small Teams</h3>
        <a href="https://www.pipedrive.com/">
            <div class="VwiC3b">
                Pipedrive is a sales CRM and pipeline management tool that helps small sales teams 
                organize leads and deals. Simple, visual, and effective CRM software.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Zoho CRM - Customer Relationship Management</h3>
        <a href="https://www.zoho.com/crm/">
            <div class="VwiC3b">
                Zoho CRM is a cloud-based customer relationship management software for managing 
                sales, marketing, and customer support activities. Free for up to 3 users.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Best CRM Software 2024 - Reviews and Comparison</h3>
        <a href="https://www.capterra.com/customer-relationship-management-software/">
            <div class="VwiC3b">
                Compare the best CRM software. Read reviews and find the perfect CRM solution 
                for your business. Salesforce, HubSpot, and Pipedrive are top-rated options.
            </div>
        </a>
    </div>
    
    <div class="c2xzTb">
        Customer Relationship Management (CRM) software helps businesses manage interactions 
        with current and potential customers. Popular CRM solutions include Salesforce, 
        HubSpot, and Pipedrive, which offer features like contact management, sales tracking, 
        and marketing automation.
    </div>
    
    <div class="AJLUJb">
        <div><a>best crm software</a></div>
        <div><a>crm software comparison</a></div>
        <div><a>free crm software</a></div>
        <div><a>salesforce alternatives</a></div>
    </div>
</body>
</html>
"""


async def mock_aiohttp_get(*args, **kwargs):
    """Mock aiohttp get request to return our mock HTML."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value=MOCK_GOOGLE_HTML)
    return mock_response


async def test_google_crm_search_mock():
    """Test Google scraper with mock CRM search results."""
    print("=" * 60)
    print("Testing Google Scraper with Mock CRM Data")
    print("=" * 60)
    
    # Initialize the scraper
    scraper = GoogleScraper()
    
    # Test keywords related to CRM
    keywords = ["CRM", "customer relationship management", "sales management"]
    idea_text = "A CRM software for small businesses to manage customer relationships and sales pipeline"
    
    print(f"Keywords: {keywords}")
    print(f"Idea text: {idea_text}")
    print("\nStarting scraping with mock data...")
    
    try:
        # Mock the aiohttp session to return our mock HTML
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__ = mock_aiohttp_get
            
            # Execute the scraping
            start_time = datetime.now()
            result = await scraper.scrape(keywords, idea_text)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"\nScraping completed in {processing_time:.2f} seconds")
            print(f"Status: {result.status}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
            
            # Display metadata
            if result.metadata:
                print("\n" + "=" * 40)
                print("METADATA")
                print("=" * 40)
                for key, value in result.metadata.items():
                    if isinstance(value, list):
                        print(f"{key}: {len(value)} items")
                        if value and len(value) <= 10:  # Show items if not too many
                            for i, item in enumerate(value, 1):
                                print(f"  {i}. {item}")
                    else:
                        print(f"{key}: {value}")
            
            # Display competitors found
            if result.competitors:
                print("\n" + "=" * 40)
                print(f"COMPETITORS FOUND ({len(result.competitors)})")
                print("=" * 40)
                for i, competitor in enumerate(result.competitors, 1):
                    print(f"\n{i}. {competitor.name}")
                    print(f"   Description: {competitor.description[:100]}...")
                    print(f"   Website: {competitor.website}")
                    print(f"   Confidence: {competitor.confidence_score:.2f}")
                    if competitor.pricing_model:
                        print(f"   Pricing: {competitor.pricing_model}")
            else:
                print("\nNo competitors found.")
            
            # Display feedback found
            if result.feedback:
                print("\n" + "=" * 40)
                print(f"FEEDBACK FOUND ({len(result.feedback)})")
                print("=" * 40)
                for i, feedback in enumerate(result.feedback, 1):
                    print(f"\n{i}. Sentiment: {feedback.sentiment} ({feedback.sentiment_score:.2f})")
                    print(f"   Text: {feedback.text[:150]}...")
                    print(f"   Source: {feedback.source_url}")
                    if feedback.author_info:
                        print(f"   Type: {feedback.author_info.get('type', 'unknown')}")
            else:
                print("\nNo feedback found.")
            
            # Save results to file for inspection
            results_data = {
                "timestamp": datetime.now().isoformat(),
                "keywords": keywords,
                "idea_text": idea_text,
                "processing_time_seconds": processing_time,
                "status": result.status.value,
                "error_message": result.error_message,
                "metadata": result.metadata,
                "competitors": [
                    {
                        "name": c.name,
                        "description": c.description,
                        "website": c.website,
                        "confidence_score": c.confidence_score,
                        "pricing_model": c.pricing_model,
                        "source": c.source
                    }
                    for c in result.competitors
                ],
                "feedback": [
                    {
                        "text": f.text,
                        "sentiment": f.sentiment,
                        "sentiment_score": f.sentiment_score,
                        "source_url": f.source_url,
                        "author_info": f.author_info
                    }
                    for f in result.feedback
                ]
            }
            
            # Save to JSON file
            output_file = f"google_crm_mock_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            print(f"\nResults saved to: {output_file}")
            
            # Summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Status: {result.status}")
            print(f"Processing time: {processing_time:.2f} seconds")
            print(f"Competitors found: {len(result.competitors)}")
            print(f"Feedback items: {len(result.feedback)}")
            if result.metadata:
                print(f"Successful queries: {result.metadata.get('successful_queries', 0)}")
                print(f"Failed queries: {result.metadata.get('failed_queries', 0)}")
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        print(f"\nTest failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_google_crm_search_mock())