"""
Test script to scrape Product Hunt for CRM products and save to CSV.
"""
import asyncio
import csv
import os
import sys
from datetime import datetime
from typing import List

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Mock the config before importing
from unittest.mock import MagicMock
sys.modules['app.config'] = MagicMock()

from app.scrapers.product_hunt_scraper import ProductHuntScraper
from app.scrapers.base_scraper import CompetitorData


async def test_product_hunt_scraping():
    """Test Product Hunt scraping for CRM products."""
    print("🚀 Starting Product Hunt CRM scraping test...")
    
    # Create scraper instance
    scraper = ProductHuntScraper()
    
    # Test keywords related to CRM
    keywords = ["CRM", "customer relationship management", "sales management"]
    idea_text = "A modern CRM system for small businesses"
    
    print(f"📊 Searching for keywords: {keywords}")
    print(f"💡 Idea context: {idea_text}")
    
    try:
        # Perform the scraping
        result = await scraper.scrape(keywords, idea_text)
        
        print(f"✅ Scraping completed with status: {result.status}")
        print(f"📈 Found {len(result.competitors)} competitors")
        
        if result.competitors:
            # Save to CSV
            csv_filename = f"product_hunt_crm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            save_to_csv(result.competitors, csv_filename)
            print(f"💾 Results saved to: {csv_filename}")
            
            # Display summary
            print("\n📋 Summary of found competitors:")
            for i, competitor in enumerate(result.competitors[:5], 1):  # Show first 5
                print(f"{i}. {competitor.name}")
                if competitor.description:
                    print(f"   Description: {competitor.description[:100]}...")
                if competitor.launch_date:
                    print(f"   Launch Date: {competitor.launch_date}")
                if competitor.founder_ceo:
                    print(f"   Founder/CEO: {competitor.founder_ceo}")
                if competitor.estimated_users:
                    print(f"   Estimated Users: {competitor.estimated_users:,}")
                if competitor.estimated_revenue:
                    print(f"   Estimated Revenue: {competitor.estimated_revenue}")
                if competitor.review_count:
                    print(f"   Reviews: {competitor.review_count} (avg: {competitor.average_rating:.1f}★)")
                if competitor.most_helpful_review:
                    print(f"   Top Review: {competitor.most_helpful_review[:80]}...")
                if competitor.website:
                    print(f"   Website: {competitor.website}")
                print(f"   Source URL: {competitor.source_url}")
                print(f"   Confidence: {competitor.confidence_score:.2f}")
                print()
        else:
            print("❌ No competitors found")
            
        if result.error_message:
            print(f"⚠️ Error message: {result.error_message}")
            
        print(f"📊 Metadata: {result.metadata}")
        
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()


def save_to_csv(competitors: List[CompetitorData], filename: str):
    """Save competitor data to CSV file."""
    fieldnames = [
        'name', 'description', 'website', 'estimated_users', 
        'estimated_revenue', 'pricing_model', 'source', 
        'source_url', 'confidence_score', 'launch_date', 
        'founder_ceo', 'most_helpful_review', 'review_count', 
        'average_rating'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for competitor in competitors:
            writer.writerow({
                'name': competitor.name,
                'description': competitor.description,
                'website': competitor.website,
                'estimated_users': competitor.estimated_users,
                'estimated_revenue': competitor.estimated_revenue,
                'pricing_model': competitor.pricing_model,
                'source': competitor.source,
                'source_url': competitor.source_url,
                'confidence_score': competitor.confidence_score,
                'launch_date': competitor.launch_date,
                'founder_ceo': competitor.founder_ceo,
                'most_helpful_review': competitor.most_helpful_review,
                'review_count': competitor.review_count,
                'average_rating': competitor.average_rating
            })


if __name__ == "__main__":
    print("🔍 Product Hunt CRM Scraper Test")
    print("=" * 50)
    
    # Run the async test
    asyncio.run(test_product_hunt_scraping())
    
    print("\n✨ Test completed!")