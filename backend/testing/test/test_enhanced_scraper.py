"""
Enhanced test script to scrape Product Hunt for CRM products with detailed information.
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


async def test_enhanced_product_hunt_scraping():
    """Test enhanced Product Hunt scraping for CRM products with detailed information."""
    print("🚀 Starting Enhanced Product Hunt CRM scraping test...")
    
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
            # Save to CSV with enhanced fields
            csv_filename = f"enhanced_crm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            save_enhanced_csv(result.competitors, csv_filename)
            print(f"💾 Enhanced results saved to: {csv_filename}")
            
            # Display detailed summary
            print("\n📋 Detailed Summary of CRM Competitors:")
            print("=" * 80)
            
            for i, competitor in enumerate(result.competitors[:5], 1):  # Show first 5
                print(f"\n{i}. 🏢 {competitor.name}")
                print("-" * 60)
                
                if competitor.description:
                    print(f"   📝 Description: {competitor.description[:150]}...")
                
                if competitor.launch_date:
                    print(f"   🚀 Launch Date: {competitor.launch_date}")
                
                if competitor.founder_ceo:
                    print(f"   👤 Founder/CEO: {competitor.founder_ceo}")
                
                if competitor.estimated_users:
                    print(f"   👥 Estimated Users: {competitor.estimated_users:,}")
                
                if competitor.estimated_revenue:
                    print(f"   💰 Estimated Revenue: {competitor.estimated_revenue}")
                
                if competitor.pricing_model and competitor.pricing_model != "Unknown":
                    print(f"   💳 Pricing Model: {competitor.pricing_model}")
                
                if competitor.review_count:
                    rating_str = f"{competitor.average_rating:.1f}★" if competitor.average_rating else "N/A"
                    print(f"   ⭐ Reviews: {competitor.review_count} reviews (avg: {rating_str})")
                
                if competitor.most_helpful_review:
                    print(f"   💬 Most Helpful Review:")
                    print(f"      {competitor.most_helpful_review}")
                
                if competitor.website:
                    print(f"   🌐 Website: {competitor.website}")
                
                print(f"   🔗 Product Hunt: {competitor.source_url}")
                print(f"   📊 Confidence Score: {competitor.confidence_score:.2f}")
            
            # Show statistics
            print(f"\n📊 Statistics:")
            print(f"   • Total competitors found: {len(result.competitors)}")
            
            # Count competitors with detailed info
            with_launch_date = sum(1 for c in result.competitors if c.launch_date)
            with_founder = sum(1 for c in result.competitors if c.founder_ceo)
            with_reviews = sum(1 for c in result.competitors if c.most_helpful_review)
            with_ratings = sum(1 for c in result.competitors if c.review_count)
            
            print(f"   • With launch date: {with_launch_date}")
            print(f"   • With founder info: {with_founder}")
            print(f"   • With helpful reviews: {with_reviews}")
            print(f"   • With rating data: {with_ratings}")
            
            # Average rating
            ratings = [c.average_rating for c in result.competitors if c.average_rating]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                print(f"   • Average rating: {avg_rating:.2f}★")
            
        else:
            print("❌ No competitors found")
            
        if result.error_message:
            print(f"⚠️ Error message: {result.error_message}")
            
        print(f"\n📊 Metadata: {result.metadata}")
        
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()


def save_enhanced_csv(competitors: List[CompetitorData], filename: str):
    """Save enhanced competitor data to CSV file."""
    fieldnames = [
        'name', 'description', 'launch_date', 'founder_ceo',
        'website', 'estimated_users', 'estimated_revenue', 
        'pricing_model', 'review_count', 'average_rating',
        'most_helpful_review', 'source', 'source_url', 
        'confidence_score'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for competitor in competitors:
            writer.writerow({
                'name': competitor.name,
                'description': competitor.description,
                'launch_date': competitor.launch_date,
                'founder_ceo': competitor.founder_ceo,
                'website': competitor.website,
                'estimated_users': competitor.estimated_users,
                'estimated_revenue': competitor.estimated_revenue,
                'pricing_model': competitor.pricing_model,
                'review_count': competitor.review_count,
                'average_rating': competitor.average_rating,
                'most_helpful_review': competitor.most_helpful_review,
                'source': competitor.source,
                'source_url': competitor.source_url,
                'confidence_score': competitor.confidence_score
            })


if __name__ == "__main__":
    print("🔍 Enhanced Product Hunt CRM Scraper Test")
    print("=" * 60)
    
    # Run the async test
    asyncio.run(test_enhanced_product_hunt_scraping())
    
    print("\n✨ Enhanced test completed!")