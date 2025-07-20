#!/usr/bin/env python3
"""
Test script for Google scraper with CSV output similar to Product Hunt.
"""
import csv
import json
from datetime import datetime
from pathlib import Path

from app.scrapers.google_scraper import GoogleScraper

# Mock HTML response that simulates Google search results for CRM
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
                Pricing starts at $25/user/month with premium features available.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>HubSpot CRM - Free CRM Software</h3>
        <a href="https://www.hubspot.com/products/crm">
            <div class="VwiC3b">
                HubSpot's free CRM software organizes, tracks, and nurtures your leads and customers. 
                Get started with our powerful, easy-to-use CRM platform. Free for small teams with 
                premium subscription options available.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Pipedrive - Sales CRM for Small Teams</h3>
        <a href="https://www.pipedrive.com/">
            <div class="VwiC3b">
                Pipedrive is a sales CRM and pipeline management tool that helps small sales teams 
                organize leads and deals. Simple, visual, and effective CRM software with 
                subscription-based pricing starting at $14.90/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Zoho CRM - Customer Relationship Management</h3>
        <a href="https://www.zoho.com/crm/">
            <div class="VwiC3b">
                Zoho CRM is a cloud-based customer relationship management software for managing 
                sales, marketing, and customer support activities. Free for up to 3 users with 
                paid plans starting at $12/user/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Monday.com CRM - Project Management & CRM</h3>
        <a href="https://monday.com/crm/">
            <div class="VwiC3b">
                Monday.com offers a comprehensive CRM solution with project management capabilities. 
                Perfect for teams that need both CRM and project tracking. One-time setup fee 
                with monthly subscription starting at $8/seat.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Freshworks CRM - Customer Experience Platform</h3>
        <a href="https://www.freshworks.com/crm/">
            <div class="VwiC3b">
                Freshworks CRM provides excellent customer experience management with AI-powered 
                insights. Great for growing businesses with trial period available and 
                competitive pricing.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Copper CRM - Google Workspace Integration</h3>
        <a href="https://www.copper.com/">
            <div class="VwiC3b">
                Copper CRM integrates seamlessly with Google Workspace. Built for Google users 
                who need powerful CRM functionality. Free trial available with subscription 
                plans starting at $25/user/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>ActiveCampaign - Email Marketing & CRM</h3>
        <a href="https://www.activecampaign.com/">
            <div class="VwiC3b">
                ActiveCampaign combines email marketing with CRM functionality. Excellent for 
                businesses focused on email campaigns and customer automation. Subscription 
                pricing with free trial period.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Best CRM Software 2024 - Reviews and Comparison</h3>
        <a href="https://www.capterra.com/customer-relationship-management-software/">
            <div class="VwiC3b">
                Compare the best CRM software. Read reviews and find the perfect CRM solution 
                for your business. Salesforce, HubSpot, and Pipedrive are top-rated options 
                with excellent user feedback and competitive pricing.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>CRM Software Reviews - G2 Ratings</h3>
        <a href="https://www.g2.com/categories/crm">
            <div class="VwiC3b">
                Discover the highest-rated CRM software based on user reviews. Compare features, 
                pricing, and user satisfaction scores. Top performers include Salesforce, 
                HubSpot, and Pipedrive with excellent ratings.
            </div>
        </a>
    </div>
    
    <div class="c2xzTb">
        Customer Relationship Management (CRM) software helps businesses manage interactions 
        with current and potential customers. Popular CRM solutions include Salesforce, 
        HubSpot, and Pipedrive, which offer excellent features like contact management, 
        sales tracking, and marketing automation with competitive pricing.
    </div>
    
    <div class="AJLUJb">
        <div><a>best crm software</a></div>
        <div><a>crm software comparison</a></div>
        <div><a>free crm software</a></div>
        <div><a>salesforce alternatives</a></div>
        <div><a>crm pricing comparison</a></div>
        <div><a>small business crm</a></div>
    </div>
</body>
</html>
"""


def create_csv_output():
    """Create CSV output from Google scraper results."""
    print("=" * 60)
    print("Google Scraper CSV Output Generation")
    print("=" * 60)
    
    # Initialize the scraper
    scraper = GoogleScraper()
    
    # Test the HTML parsing directly
    query = "CRM software"
    search_results = scraper._parse_search_results(MOCK_GOOGLE_HTML, query)
    
    # Extract competitors and feedback
    competitors = scraper._extract_competitors(search_results, query)
    feedback = scraper._extract_feedback(search_results, query)
    
    print(f"Extracted {len(competitors)} competitors and {len(feedback)} feedback items")
    
    # Create timestamp for file naming
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create competitors CSV
    competitors_file = f"google_crm_competitors_{timestamp}.csv"
    
    with open(competitors_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'name',
            'description', 
            'website',
            'source',
            'source_url',
            'confidence_score',
            'pricing_model',
            'estimated_users',
            'estimated_revenue',
            'launch_date',
            'founder_ceo',
            'most_helpful_review',
            'review_count',
            'average_rating'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for competitor in competitors:
            writer.writerow({
                'name': competitor.name,
                'description': competitor.description,
                'website': competitor.website,
                'source': competitor.source,
                'source_url': competitor.source_url,
                'confidence_score': competitor.confidence_score,
                'pricing_model': competitor.pricing_model or '',
                'estimated_users': competitor.estimated_users or '',
                'estimated_revenue': competitor.estimated_revenue or '',
                'launch_date': competitor.launch_date or '',
                'founder_ceo': competitor.founder_ceo or '',
                'most_helpful_review': competitor.most_helpful_review or '',
                'review_count': competitor.review_count or '',
                'average_rating': competitor.average_rating or ''
            })
    
    print(f"✅ Competitors CSV saved: {competitors_file}")
    
    # Create feedback CSV
    feedback_file = f"google_crm_feedback_{timestamp}.csv"
    
    with open(feedback_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'text',
            'sentiment',
            'sentiment_score',
            'source',
            'source_url',
            'author_username',
            'author_type',
            'query',
            'result_title'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for feedback_item in feedback:
            author_info = feedback_item.author_info or {}
            writer.writerow({
                'text': feedback_item.text,
                'sentiment': feedback_item.sentiment,
                'sentiment_score': feedback_item.sentiment_score,
                'source': feedback_item.source,
                'source_url': feedback_item.source_url,
                'author_username': author_info.get('username', ''),
                'author_type': author_info.get('type', ''),
                'query': author_info.get('query', ''),
                'result_title': author_info.get('title', '')
            })
    
    print(f"✅ Feedback CSV saved: {feedback_file}")
    
    # Create search results CSV (raw data)
    search_results_file = f"google_crm_search_results_{timestamp}.csv"
    
    with open(search_results_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'title',
            'link',
            'snippet',
            'query',
            'is_competitor',
            'has_feedback_indicators',
            'extracted_company_name',
            'confidence_score'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in search_results['organic_results']:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            link = result.get('link', '')
            
            # Check if this result was identified as a competitor
            is_competitor = scraper._is_likely_competitor(title, snippet, query)
            has_feedback = scraper._contains_feedback_indicators(title, snippet)
            company_name = scraper._extract_company_name(title, link)
            confidence = scraper._calculate_competitor_confidence(title, snippet, query)
            
            writer.writerow({
                'title': title,
                'link': link,
                'snippet': snippet,
                'query': query,
                'is_competitor': is_competitor,
                'has_feedback_indicators': has_feedback,
                'extracted_company_name': company_name or '',
                'confidence_score': confidence
            })
    
    print(f"✅ Search results CSV saved: {search_results_file}")
    
    # Create summary CSV
    summary_file = f"google_crm_summary_{timestamp}.csv"
    
    with open(summary_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'metric',
            'value',
            'description'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Calculate summary metrics
        total_results = len(search_results['organic_results'])
        competitor_results = len(competitors)
        feedback_results = len(feedback)
        has_featured_snippet = bool(search_results.get('featured_snippet'))
        related_searches_count = len(search_results.get('related_searches', []))
        
        # Pricing model distribution
        pricing_models = {}
        for comp in competitors:
            model = comp.pricing_model or 'Unknown'
            pricing_models[model] = pricing_models.get(model, 0) + 1
        
        # Confidence score statistics
        confidence_scores = [c.confidence_score for c in competitors]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Sentiment distribution
        sentiment_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
        for fb in feedback:
            sentiment_dist[fb.sentiment] = sentiment_dist.get(fb.sentiment, 0) + 1
        
        summary_data = [
            ('total_search_results', total_results, 'Total organic search results found'),
            ('competitors_extracted', competitor_results, 'Number of competitors identified'),
            ('feedback_items', feedback_results, 'Number of feedback items extracted'),
            ('featured_snippet_found', has_featured_snippet, 'Whether a featured snippet was found'),
            ('related_searches_count', related_searches_count, 'Number of related search suggestions'),
            ('average_confidence_score', round(avg_confidence, 3), 'Average confidence score for competitors'),
            ('free_pricing_count', pricing_models.get('Free', 0), 'Competitors with free pricing'),
            ('freemium_pricing_count', pricing_models.get('Freemium', 0), 'Competitors with freemium pricing'),
            ('subscription_pricing_count', pricing_models.get('Subscription', 0), 'Competitors with subscription pricing'),
            ('positive_feedback_count', sentiment_dist['positive'], 'Positive feedback items'),
            ('negative_feedback_count', sentiment_dist['negative'], 'Negative feedback items'),
            ('neutral_feedback_count', sentiment_dist['neutral'], 'Neutral feedback items'),
        ]
        
        for metric, value, description in summary_data:
            writer.writerow({
                'metric': metric,
                'value': value,
                'description': description
            })
    
    print(f"✅ Summary CSV saved: {summary_file}")
    
    # Display summary
    print("\n" + "=" * 40)
    print("CSV GENERATION SUMMARY")
    print("=" * 40)
    print(f"📊 Total search results: {total_results}")
    print(f"🏢 Competitors found: {competitor_results}")
    print(f"💬 Feedback items: {feedback_results}")
    print(f"⭐ Featured snippet: {'Yes' if has_featured_snippet else 'No'}")
    print(f"🔍 Related searches: {related_searches_count}")
    print(f"📈 Average confidence: {avg_confidence:.3f}")
    
    print(f"\n📁 Files created:")
    print(f"   • {competitors_file}")
    print(f"   • {feedback_file}")
    print(f"   • {search_results_file}")
    print(f"   • {summary_file}")
    
    # Display top competitors
    print(f"\n🏆 Top Competitors Found:")
    for i, comp in enumerate(competitors[:5], 1):
        pricing = f" ({comp.pricing_model})" if comp.pricing_model else ""
        print(f"   {i}. {comp.name}{pricing} - {comp.confidence_score:.2f}")
    
    # Display pricing model distribution
    if pricing_models:
        print(f"\n💰 Pricing Model Distribution:")
        for model, count in pricing_models.items():
            print(f"   • {model}: {count} competitors")
    
    # Display sentiment distribution
    print(f"\n😊 Sentiment Distribution:")
    for sentiment, count in sentiment_dist.items():
        emoji = "😊" if sentiment == "positive" else "😞" if sentiment == "negative" else "😐"
        print(f"   {emoji} {sentiment.title()}: {count} items")
    
    return {
        'competitors_file': competitors_file,
        'feedback_file': feedback_file,
        'search_results_file': search_results_file,
        'summary_file': summary_file,
        'total_competitors': competitor_results,
        'total_feedback': feedback_results
    }


if __name__ == "__main__":
    result = create_csv_output()
    print(f"\n✅ CSV generation completed successfully!")
    print(f"📈 Generated {result['total_competitors']} competitor records")
    print(f"💬 Generated {result['total_feedback']} feedback records")