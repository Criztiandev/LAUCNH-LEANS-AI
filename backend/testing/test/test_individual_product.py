"""
Test script to examine a single Product Hunt product in detail.
"""
import asyncio
import sys
from unittest.mock import MagicMock

# Mock the config
sys.modules['app.config'] = MagicMock()

from app.scrapers.product_hunt_scraper import ProductHuntScraper
from app.scrapers.base_scraper import CompetitorData


async def test_individual_product():
    """Test detailed extraction for a single product."""
    print("🔍 Testing individual product extraction...")
    
    scraper = ProductHuntScraper()
    
    # Create a test competitor with just the source URL
    competitor = CompetitorData(
        name="folk",
        source="Product Hunt",
        source_url="https://www.producthunt.com/posts/folk-2"
    )
    
    print(f"📡 Extracting detailed info for: {competitor.name}")
    print(f"🔗 URL: {competitor.source_url}")
    
    try:
        # Create session
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=30)
        scraper.session = aiohttp.ClientSession(
            headers=scraper.headers,
            timeout=timeout
        )
        
        # Enrich the competitor data
        await scraper._enrich_competitor_data(competitor)
        
        # Display results
        print("\n📋 Extracted Information:")
        print("=" * 50)
        print(f"🏢 Name: {competitor.name}")
        print(f"📝 Description: {competitor.description}")
        print(f"🚀 Launch Date: {competitor.launch_date}")
        print(f"👤 Founder/CEO: {competitor.founder_ceo}")
        print(f"👥 Estimated Users: {competitor.estimated_users}")
        print(f"💰 Estimated Revenue: {competitor.estimated_revenue}")
        print(f"💳 Pricing Model: {competitor.pricing_model}")
        print(f"⭐ Review Count: {competitor.review_count}")
        print(f"📊 Average Rating: {competitor.average_rating}")
        print(f"🌐 Website: {competitor.website}")
        print(f"📈 Confidence Score: {competitor.confidence_score}")
        
        if competitor.most_helpful_review:
            print(f"\n💬 Most Helpful Review:")
            print(f"   {competitor.most_helpful_review}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.session:
            await scraper.session.close()


if __name__ == "__main__":
    print("🧪 Individual Product Test")
    print("=" * 40)
    
    asyncio.run(test_individual_product())
    
    print("\n✨ Test completed!")