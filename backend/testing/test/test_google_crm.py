#!/usr/bin/env python3
"""
Test script for Google scraper with CRM search.
"""
import asyncio
import json
import logging
from datetime import datetime

from app.scrapers.google_scraper import GoogleScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_google_crm_search():
    """Test Google scraper with CRM-related keywords."""
    print("=" * 60)
    print("Testing Google Scraper with CRM Search")
    print("=" * 60)
    
    # Initialize the scraper
    scraper = GoogleScraper()
    
    # Test keywords related to CRM
    keywords = ["CRM", "customer relationship management", "sales management"]
    idea_text = "A CRM software for small businesses to manage customer relationships and sales pipeline"
    
    print(f"Keywords: {keywords}")
    print(f"Idea text: {idea_text}")
    print("\nStarting scraping...")
    
    try:
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
        output_file = f"google_crm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    asyncio.run(test_google_crm_search())