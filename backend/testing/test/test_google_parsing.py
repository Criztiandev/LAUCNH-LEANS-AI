#!/usr/bin/env python3
"""
Test script to demonstrate Google scraper parsing functionality.
"""
import json
from datetime import datetime

from app.scrapers.google_scraper import GoogleScraper

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
                Get started with our powerful, easy-to-use CRM platform. Free for small teams.
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
        HubSpot, and Pipedrive, which offer excellent features like contact management, 
        sales tracking, and marketing automation.
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


def test_google_parsing():
    """Test Google scraper parsing functionality with mock HTML."""
    print("=" * 60)
    print("Testing Google Scraper HTML Parsing")
    print("=" * 60)
    
    # Initialize the scraper
    scraper = GoogleScraper()
    
    # Test the HTML parsing directly
    query = "CRM software"
    search_results = scraper._parse_search_results(MOCK_GOOGLE_HTML, query)
    
    print(f"Query: {query}")
    print(f"Organic results found: {len(search_results['organic_results'])}")
    print(f"Featured snippet: {'Yes' if search_results['featured_snippet'] else 'No'}")
    print(f"Related searches: {len(search_results['related_searches'])}")
    
    # Display organic results
    print("\n" + "=" * 40)
    print("ORGANIC RESULTS")
    print("=" * 40)
    for i, result in enumerate(search_results['organic_results'], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['link']}")
        print(f"   Snippet: {result['snippet'][:100]}...")
    
    # Test competitor extraction
    competitors = scraper._extract_competitors(search_results, query)
    
    print("\n" + "=" * 40)
    print(f"COMPETITORS EXTRACTED ({len(competitors)})")
    print("=" * 40)
    for i, competitor in enumerate(competitors, 1):
        print(f"\n{i}. {competitor.name}")
        print(f"   Description: {competitor.description[:100]}...")
        print(f"   Website: {competitor.website}")
        print(f"   Confidence: {competitor.confidence_score:.2f}")
        if competitor.pricing_model:
            print(f"   Pricing: {competitor.pricing_model}")
    
    # Test feedback extraction
    feedback = scraper._extract_feedback(search_results, query)
    
    print("\n" + "=" * 40)
    print(f"FEEDBACK EXTRACTED ({len(feedback)})")
    print("=" * 40)
    for i, feedback_item in enumerate(feedback, 1):
        print(f"\n{i}. Sentiment: {feedback_item.sentiment} ({feedback_item.sentiment_score:.2f})")
        print(f"   Text: {feedback_item.text[:100]}...")
        print(f"   Type: {feedback_item.author_info.get('type', 'unknown')}")
    
    # Test query generation
    keywords = ["CRM", "customer relationship management", "sales management"]
    idea_text = "A CRM software for small businesses to manage customer relationships and sales pipeline"
    
    queries = scraper._generate_search_queries(keywords, idea_text)
    
    print("\n" + "=" * 40)
    print(f"GENERATED QUERIES ({len(queries)})")
    print("=" * 40)
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    # Test helper functions
    print("\n" + "=" * 40)
    print("HELPER FUNCTION TESTS")
    print("=" * 40)
    
    # Test company name extraction
    test_titles = [
        "Salesforce - #1 CRM Software",
        "HubSpot CRM - Free CRM Software", 
        "Best CRM Software 2024 - Reviews"
    ]
    
    test_urls = [
        "https://www.salesforce.com/",
        "https://www.hubspot.com/products/crm",
        "https://www.capterra.com/crm/"
    ]
    
    print("Company name extraction:")
    for title, url in zip(test_titles, test_urls):
        name = scraper._extract_company_name(title, url)
        print(f"  '{title}' -> '{name}'")
    
    # Test sentiment analysis
    test_texts = [
        "This CRM software is amazing and I love using it!",
        "Terrible CRM tool, worst experience ever, hate it",
        "This is a CRM software for managing customers"
    ]
    
    print("\nSentiment analysis:")
    for text in test_texts:
        sentiment, score = scraper._analyze_sentiment(text)
        print(f"  '{text[:50]}...' -> {sentiment} ({score:.2f})")
    
    # Save parsing results
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "HTML Parsing Test",
        "query": query,
        "organic_results_count": len(search_results['organic_results']),
        "competitors_extracted": len(competitors),
        "feedback_extracted": len(feedback),
        "queries_generated": len(queries),
        "organic_results": search_results['organic_results'],
        "competitors": [
            {
                "name": c.name,
                "description": c.description,
                "website": c.website,
                "confidence_score": c.confidence_score,
                "pricing_model": c.pricing_model
            }
            for c in competitors
        ],
        "feedback": [
            {
                "text": f.text,
                "sentiment": f.sentiment,
                "sentiment_score": f.sentiment_score,
                "author_info": f.author_info
            }
            for f in feedback
        ],
        "generated_queries": queries
    }
    
    # Save to JSON file
    output_file = f"google_parsing_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nParsing test results saved to: {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("PARSING TEST SUMMARY")
    print("=" * 60)
    print(f"Organic results parsed: {len(search_results['organic_results'])}")
    print(f"Competitors extracted: {len(competitors)}")
    print(f"Feedback items extracted: {len(feedback)}")
    print(f"Search queries generated: {len(queries)}")
    print(f"Featured snippet found: {'Yes' if search_results['featured_snippet'] else 'No'}")
    print(f"Related searches found: {len(search_results['related_searches'])}")


if __name__ == "__main__":
    test_google_parsing()