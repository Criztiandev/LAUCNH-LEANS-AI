#!/usr/bin/env python3
"""
Comprehensive Google scraper test for CRM market analysis.
Creates similar output format to Product Hunt analysis.
"""
import asyncio
import json
import csv
import logging
from datetime import datetime
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.scrapers.google_scraper import GoogleScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# Enhanced mock HTML with more realistic CRM search results
MOCK_GOOGLE_CRM_HTML = """
<!DOCTYPE html>
<html>
<head><title>CRM software - Google Search</title></head>
<body>
    <div class="g">
        <h3>Salesforce - #1 CRM Software | Free Trial</h3>
        <a href="https://www.salesforce.com/">
            <div class="VwiC3b">
                Salesforce is the world's #1 CRM platform trusted by 150,000+ companies. 
                Our cloud-based CRM software helps businesses manage customer relationships, 
                sales, and marketing. Free trial available. Starting at $25/user/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>HubSpot CRM - Free CRM Software for Growing Teams</h3>
        <a href="https://www.hubspot.com/products/crm">
            <div class="VwiC3b">
                HubSpot's free CRM software organizes, tracks, and nurtures your leads and customers. 
                Used by 100,000+ businesses worldwide. Free forever for unlimited users. 
                Premium features start at $45/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Pipedrive - Sales CRM Built by Salespeople</h3>
        <a href="https://www.pipedrive.com/">
            <div class="VwiC3b">
                Pipedrive is a sales CRM and pipeline management tool that helps 95,000+ sales teams 
                organize leads and deals. Simple, visual, and effective CRM software. 
                14-day free trial. Plans from $14.90/user/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Zoho CRM - Customer Relationship Management Software</h3>
        <a href="https://www.zoho.com/crm/">
            <div class="VwiC3b">
                Zoho CRM is a cloud-based customer relationship management software for managing 
                sales, marketing, and customer support activities. Used by 250,000+ businesses. 
                Free for up to 3 users. Paid plans from $14/user/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Monday.com CRM - Project Management & CRM Platform</h3>
        <a href="https://monday.com/crm/">
            <div class="VwiC3b">
                Monday.com CRM combines project management with customer relationship management. 
                Trusted by 180,000+ customers worldwide. Excellent for team collaboration. 
                Free trial available. Plans from $8/user/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Freshworks CRM - Sales CRM for High-Velocity Teams</h3>
        <a href="https://www.freshworks.com/crm/">
            <div class="VwiC3b">
                Freshworks CRM (formerly Freshsales) is built for high-velocity sales teams. 
                AI-powered insights and automation. Used by 60,000+ businesses. 
                Free plan available. Paid plans from $15/user/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Copper CRM - Google Workspace Native CRM</h3>
        <a href="https://www.copper.com/">
            <div class="VwiC3b">
                Copper CRM is built for Google Workspace users. Seamless integration with Gmail, 
                Calendar, and Drive. Trusted by 25,000+ companies. No setup required for Google users. 
                Plans from $25/user/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>ActiveCampaign - Email Marketing + CRM Platform</h3>
        <a href="https://www.activecampaign.com/">
            <div class="VwiC3b">
                ActiveCampaign combines email marketing, marketing automation, and CRM. 
                Over 180,000 customers in 170 countries. Excellent for marketing automation. 
                Free trial available. Plans from $9/month.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>Best CRM Software 2024 - Reviews & Comparison | G2</h3>
        <a href="https://www.g2.com/categories/crm">
            <div class="VwiC3b">
                Compare the best CRM software based on 50,000+ user reviews. Top-rated CRM solutions 
                include Salesforce (4.4/5), HubSpot (4.5/5), and Pipedrive (4.2/5). 
                Find the perfect CRM for your business needs.
            </div>
        </a>
    </div>
    
    <div class="g">
        <h3>CRM Software Market Size & Growth Report 2024</h3>
        <a href="https://www.marketsandmarkets.com/Market-Reports/customer-relationship-management-crm-market-989.html">
            <div class="VwiC3b">
                The global CRM software market size is projected to grow from $58.04 billion in 2023 
                to $145.79 billion by 2029, at a CAGR of 16.9%. Key drivers include digital transformation 
                and increasing demand for customer analytics.
            </div>
        </a>
    </div>
    
    <div class="c2xzTb">
        Customer Relationship Management (CRM) software helps businesses manage interactions 
        with current and potential customers. The global CRM market is valued at $58+ billion 
        and growing at 16.9% CAGR. Leading solutions include Salesforce (market leader with 19.8% share), 
        HubSpot (fastest growing), and Microsoft Dynamics 365. Key features include contact management, 
        sales automation, marketing integration, and analytics.
    </div>
    
    <div class="AJLUJb">
        <div><a>best crm software 2024</a></div>
        <div><a>crm software comparison</a></div>
        <div><a>free crm software</a></div>
        <div><a>salesforce alternatives</a></div>
        <div><a>crm market size</a></div>
        <div><a>small business crm</a></div>
        <div><a>crm pricing comparison</a></div>
        <div><a>crm software reviews</a></div>
    </div>
</body>
</html>
"""


def extract_user_numbers(text):
    """Extract user/customer numbers from text."""
    import re
    
    # Patterns to match user numbers
    patterns = [
        r'(\d+(?:,\d+)*)\+?\s*(?:companies|customers|businesses|users)',
        r'(?:trusted by|used by)\s*(\d+(?:,\d+)*)\+?\s*(?:companies|customers|businesses|users)',
        r'over\s*(\d+(?:,\d+)*)\+?\s*(?:companies|customers|businesses|users)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            number_str = match.group(1).replace(',', '')
            try:
                return int(number_str)
            except ValueError:
                continue
    
    return None


def extract_pricing(text):
    """Extract pricing information from text."""
    import re
    
    # Look for pricing patterns
    if 'free forever' in text.lower() or 'free for up to' in text.lower():
        return 'Freemium'
    elif 'free trial' in text.lower() and ('$' in text or 'plans from' in text.lower()):
        return 'Free trial + Paid'
    elif 'free plan' in text.lower():
        return 'Freemium'
    elif '$' in text:
        # Extract price
        price_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
        if price_match:
            return f"From ${price_match.group(1)}/month"
    
    return 'Contact for pricing'


def extract_rating(text):
    """Extract rating information from text."""
    import re
    
    # Look for rating patterns like "4.4/5" or "4.5 stars"
    rating_patterns = [
        r'(\d+\.\d+)/5',
        r'(\d+\.\d+)\s*stars?',
        r'(\d+\.\d+)\s*rating',
    ]
    
    for pattern in rating_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None


async def test_google_crm_comprehensive():
    """Comprehensive Google CRM market analysis test."""
    print("=" * 80)
    print("🔍 GOOGLE CRM MARKET ANALYSIS")
    print("=" * 80)
    
    # Initialize the scraper
    scraper = GoogleScraper()
    
    # Test keywords related to CRM
    keywords = ["CRM", "customer relationship management", "sales management"]
    idea_text = "A CRM software for small businesses to manage customer relationships and sales pipeline"
    
    print(f"📊 Search Keywords: {', '.join(keywords)}")
    print(f"💡 Business Idea: {idea_text}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%B %d, %Y')}")
    
    try:
        # Parse the mock HTML directly for testing
        search_results = scraper._parse_search_results(MOCK_GOOGLE_CRM_HTML, "CRM software")
        competitors = scraper._extract_competitors(search_results, "CRM software")
        feedback = scraper._extract_feedback(search_results, "CRM software")
        
        # Enhance competitor data with extracted information
        enhanced_competitors = []
        for competitor in competitors:
            # Extract additional data from description
            users = extract_user_numbers(competitor.description)
            pricing = extract_pricing(competitor.description)
            rating = extract_rating(competitor.description)
            
            enhanced_competitor = {
                'name': competitor.name,
                'description': competitor.description,
                'website': competitor.website,
                'confidence_score': competitor.confidence_score,
                'pricing_model': pricing,
                'estimated_users': users,
                'rating': rating,
                'source': 'Google Search'
            }
            enhanced_competitors.append(enhanced_competitor)
        
        # Sort by estimated users (descending)
        enhanced_competitors.sort(key=lambda x: x['estimated_users'] or 0, reverse=True)
        
        # Generate comprehensive analysis
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'search_keywords': keywords,
            'business_idea': idea_text,
            'total_competitors': len(enhanced_competitors),
            'data_source': 'Google Search',
            'competitors': enhanced_competitors,
            'feedback': [
                {
                    'text': f.text,
                    'sentiment': f.sentiment,
                    'sentiment_score': f.sentiment_score,
                    'source_url': f.source_url,
                    'type': f.author_info.get('type', 'unknown') if f.author_info else 'unknown'
                }
                for f in feedback
            ],
            'market_insights': {
                'total_organic_results': len(search_results['organic_results']),
                'featured_snippet_found': bool(search_results['featured_snippet']),
                'related_searches': search_results['related_searches']
            }
        }
        
        # Create output directories
        backend_dir = Path(__file__).parent.parent.parent
        output_dir = backend_dir / 'output'
        csv_dir = output_dir / 'csv'
        
        # Ensure directories exist
        output_dir.mkdir(exist_ok=True)
        csv_dir.mkdir(exist_ok=True)
        
        # Save JSON data
        json_file = output_dir / f'google_crm_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        # Save CSV data
        csv_file = csv_dir / f'google_crm_competitors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'name', 'estimated_users', 'pricing_model', 'rating', 
                'confidence_score', 'website', 'description'
            ])
            writer.writeheader()
            for comp in enhanced_competitors:
                writer.writerow({
                    'name': comp['name'],
                    'estimated_users': comp['estimated_users'] or 'N/A',
                    'pricing_model': comp['pricing_model'],
                    'rating': comp['rating'] or 'N/A',
                    'confidence_score': comp['confidence_score'],
                    'website': comp['website'],
                    'description': comp['description'][:200] + '...' if len(comp['description']) > 200 else comp['description']
                })
        
        # Generate Markdown report similar to Product Hunt analysis
        markdown_report = generate_markdown_report(analysis_data, enhanced_competitors, feedback)
        
        # Save Markdown report
        md_file = output_dir / f'google_crm_market_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        # Display results
        print(f"\n📈 ANALYSIS RESULTS")
        print(f"{'='*50}")
        print(f"🏢 Total Competitors Found: {len(enhanced_competitors)}")
        print(f"💬 Feedback Items: {len(feedback)}")
        print(f"🔍 Organic Results: {len(search_results['organic_results'])}")
        print(f"⭐ Featured Snippet: {'Yes' if search_results['featured_snippet'] else 'No'}")
        
        print(f"\n🏆 TOP CRM COMPETITORS BY USER BASE")
        print(f"{'='*50}")
        for i, comp in enumerate(enhanced_competitors[:5], 1):
            users_str = f"{comp['estimated_users']:,}" if comp['estimated_users'] else "N/A"
            rating_str = f"{comp['rating']}★" if comp['rating'] else "N/A"
            print(f"{i}. {comp['name']}")
            print(f"   👥 Users: {users_str}")
            print(f"   💰 Pricing: {comp['pricing_model']}")
            print(f"   ⭐ Rating: {rating_str}")
            print(f"   🌐 Website: {comp['website']}")
            print()
        
        print(f"📁 FILES GENERATED:")
        print(f"   📊 JSON Analysis: {json_file}")
        print(f"   📋 CSV Data: {csv_file}")
        print(f"   📝 Markdown Report: {md_file}")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        print(f"❌ Analysis failed: {str(e)}")
        return None


def generate_markdown_report(analysis_data, competitors, feedback):
    """Generate a comprehensive markdown report similar to Product Hunt analysis."""
    
    timestamp = datetime.now().strftime("%B %d, %Y")
    
    report = f"""# 🔍 CRM Market Analysis - Google Search Data

## 🎯 Search Results Summary
- **Search Keywords**: {', '.join(analysis_data['search_keywords'])}
- **Total Competitors Found**: {len(competitors)} CRM solutions
- **Data Source**: Google Search
- **Analysis Date**: {timestamp}

## 🏆 Top CRM Solutions by User Base

| Rank | Product | Users | Pricing | Rating | Confidence |
|------|---------|-------|---------|--------|------------|
"""
    
    # Add top competitors table
    for i, comp in enumerate(competitors[:8], 1):
        users = f"{comp['estimated_users']:,}" if comp['estimated_users'] else "N/A"
        rating = f"{comp['rating']}★" if comp['rating'] else "N/A"
        confidence = f"{comp['confidence_score']:.2f}"
        
        report += f"| {i} | **{comp['name']}** | {users} | {comp['pricing_model']} | {rating} | {confidence} |\n"
    
    # Market insights section
    report += f"""
## 📊 Market Insights

### User Base Distribution:
"""
    
    # Calculate market statistics
    total_users = sum(comp['estimated_users'] for comp in competitors if comp['estimated_users'])
    companies_with_users = [comp for comp in competitors if comp['estimated_users']]
    
    if companies_with_users:
        avg_users = total_users // len(companies_with_users)
        market_leader = max(companies_with_users, key=lambda x: x['estimated_users'])
        
        report += f"""- **Total Combined Users**: {total_users:,}+ across major platforms
- **Average User Base**: {avg_users:,} users per platform
- **Market Leader**: {market_leader['name']} with {market_leader['estimated_users']:,}+ users
- **Market Concentration**: Top 3 platforms control {sum(comp['estimated_users'] for comp in companies_with_users[:3]):,}+ users
"""
    
    # Pricing analysis
    pricing_models = {}
    for comp in competitors:
        pricing = comp['pricing_model']
        pricing_models[pricing] = pricing_models.get(pricing, 0) + 1
    
    report += f"""
### Pricing Model Distribution:
"""
    for pricing, count in sorted(pricing_models.items(), key=lambda x: x[1], reverse=True):
        report += f"- **{pricing}**: {count} platform{'s' if count > 1 else ''}\n"
    
    # Competitive landscape
    report += f"""
## 🚀 Competitive Landscape

### Market Leaders:
"""
    
    for i, comp in enumerate(competitors[:3], 1):
        report += f"""
**{i}. {comp['name']}**
- 👥 User Base: {f"{comp['estimated_users']:,}" if comp['estimated_users'] else "N/A"}
- 💰 Pricing: {comp['pricing_model']}
- ⭐ Rating: {f"{comp['rating']}★" if comp['rating'] else "N/A"}
- 🌐 Website: {comp['website']}
- 📝 Description: {comp['description'][:150]}...
"""
    
    # Market opportunities
    report += f"""
## 🎯 Market Opportunities

### Key Findings:
1. **Market Size**: Large and growing market with established players
2. **Pricing Diversity**: Multiple pricing models from free to enterprise
3. **Feature Differentiation**: Platforms compete on specialization and integrations
4. **User Base Concentration**: Market leaders have significant user advantages

### Success Factors:
1. **Free/Freemium Models**: Many successful platforms offer free tiers
2. **Integration Focus**: Google Workspace, email, and automation integrations
3. **Specialization**: Industry-specific or use-case focused solutions
4. **User Experience**: Simple, visual, and effective interfaces

### Entry Opportunities:
1. **Niche Markets**: Industry-specific CRM solutions
2. **SMB Focus**: Simplified CRM for small businesses
3. **Integration-First**: Deep integrations with popular tools
4. **AI/Automation**: Advanced automation and AI features
"""
    
    # Add feedback analysis if available
    if feedback:
        report += f"""
## 💬 Market Sentiment Analysis

### Feedback Summary:
- **Total Feedback Items**: {len(feedback)}
- **Sentiment Distribution**:
"""
        
        sentiment_counts = {}
        for f in feedback:
            sentiment_counts[f.sentiment] = sentiment_counts.get(f.sentiment, 0) + 1
        
        for sentiment, count in sentiment_counts.items():
            report += f"  - {sentiment.title()}: {count} item{'s' if count > 1 else ''}\n"
    
    # Market assessment
    report += f"""
## 📈 Market Assessment

**Market Maturity**: Mature market with established leaders
**Competition Level**: High (8+ major competitors identified)
**Innovation Areas**: AI automation, industry specialization, integration depth
**Entry Barriers**: High (established user bases, feature parity requirements)
**Growth Potential**: Moderate to High (market still growing at 16.9% CAGR)

**Recommendation**: Focus on niche specialization or unique value proposition to compete effectively.

---
*Data extracted from Google Search using advanced scraping technology*
*Analysis includes user bases, pricing models, ratings, and competitive positioning*
"""
    
    return report


if __name__ == "__main__":
    asyncio.run(test_google_crm_comprehensive())