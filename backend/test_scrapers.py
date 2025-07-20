#!/usr/bin/env python3
"""
Test script for scrapers with command-line arguments.
"""
import asyncio
import json
import csv
import argparse
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the parent directory to sys.path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.scrapers.product_hunt_scraper import ProductHuntScraper
from app.scrapers.google_scraper import GoogleScraper
from app.scrapers.reddit_scraper import RedditScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_product_hunt_scraper(query: str):
    """Test Product Hunt scraper with the given query."""
    print("=" * 80)
    print(f"🚀 PRODUCT HUNT SCRAPER TEST: {query}")
    print("=" * 80)
    
    # Initialize the scraper
    scraper = ProductHuntScraper()
    
    # Generate keywords from query
    keywords = query.split()
    idea_text = f"A {query} platform for businesses"
    
    print(f"📊 Search Keywords: {', '.join(keywords)}")
    print(f"💡 Business Idea: {idea_text}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%B %d, %Y')}")
    print("\nStarting Product Hunt scraping...")
    
    try:
        # Execute the scraping
        start_time = datetime.now()
        result = await scraper.scrape(keywords, idea_text)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Scraping completed in {processing_time:.2f} seconds")
        print(f"📊 Status: {result.status}")
        
        if result.error_message:
            print(f"❌ Error: {result.error_message}")
        
        # Process competitor data
        competitors = result.competitors
        
        # Process feedback data
        feedback_data = result.feedback
        
        # Generate analysis data
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'search_keywords': keywords,
            'business_idea': idea_text,
            'total_competitors': len(competitors),
            'total_feedback': len(feedback_data),
            'data_source': 'Product Hunt',
            'processing_time_seconds': processing_time,
            'scraping_status': result.status.value,
            'competitors': [comp.__dict__ for comp in competitors],
            'feedback': [fb.__dict__ for fb in feedback_data],
            'metadata': result.metadata
        }
        
        # Create output directories
        output_dir = Path('/backend/output')
        csv_dir = output_dir / 'csv'
        
        # Ensure directories exist
        output_dir.mkdir(exist_ok=True)
        csv_dir.mkdir(exist_ok=True)
        
        # Save JSON data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = output_dir / f'product_hunt_{query.replace(" ", "_")}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        # Save CSV data for competitors
        csv_file = csv_dir / f'product_hunt_{query.replace(" ", "_")}_{timestamp}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'name', 'description', 'website', 'estimated_users', 'estimated_revenue', 
                'pricing_model', 'confidence_score', 'source', 'source_url', 'launch_date',
                'founder_ceo', 'review_count', 'average_rating', 'most_helpful_review'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for comp in competitors:
                writer.writerow({
                    'name': comp.name,
                    'description': comp.description or 'N/A',
                    'website': comp.website or 'N/A',
                    'estimated_users': comp.estimated_users or 'N/A',
                    'estimated_revenue': comp.estimated_revenue or 'N/A',
                    'pricing_model': comp.pricing_model or 'N/A',
                    'confidence_score': comp.confidence_score,
                    'source': comp.source,
                    'source_url': comp.source_url or 'N/A',
                    'launch_date': comp.launch_date or 'N/A',
                    'founder_ceo': comp.founder_ceo or 'N/A',
                    'review_count': comp.review_count or 'N/A',
                    'average_rating': comp.average_rating or 'N/A',
                    'most_helpful_review': comp.most_helpful_review or 'N/A'
                })
        
        # Display results
        print(f"\n📈 ANALYSIS RESULTS")
        print(f"{'='*50}")
        print(f"🏢 Total Competitors Found: {len(competitors)}")
        print(f"💬 Feedback Items: {len(feedback_data)}")
        print(f"⏱️ Processing Time: {processing_time:.2f} seconds")
        
        if result.metadata:
            print(f"🔍 Keywords Searched: {result.metadata.get('keywords_searched', 'N/A')}")
            print(f"📊 Total Found: {result.metadata.get('total_found', 'N/A')}")
        
        if competitors:
            print(f"\n🏆 TOP COMPETITORS FROM PRODUCT HUNT")
            print(f"{'='*50}")
            for i, comp in enumerate(competitors[:5], 1):
                users_str = f"{comp.estimated_users:,}" if comp.estimated_users else "N/A"
                revenue_str = comp.estimated_revenue or "N/A"
                print(f"{i}. {comp.name}")
                print(f"   👥 Users: {users_str}")
                print(f"   💰 Revenue: {revenue_str}")
                print(f"   🌐 Website: {comp.website or 'N/A'}")
                print(f"   📝 Description: {comp.description[:100]}..." if comp.description and len(comp.description) > 100 else f"   📝 Description: {comp.description or 'N/A'}")
                
                # Display reviews/comments if available
                if comp.most_helpful_review:
                    print(f"   💬 Top Review: \"{comp.most_helpful_review}\"")
                
                # Display ratings if available
                if comp.average_rating:
                    print(f"   ⭐ Rating: {comp.average_rating} ({comp.review_count} reviews)")
                
                # Display launch date and founder if available
                if comp.launch_date:
                    print(f"   🚀 Launched: {comp.launch_date}")
                if comp.founder_ceo:
                    print(f"   👤 Founder/CEO: {comp.founder_ceo}")
                
                print()
        else:
            print("\n❌ No competitors found")
        
        # Generate markdown report
        markdown_report = generate_product_hunt_markdown_report(query, analysis_data, competitors, feedback_data)
        md_file = output_dir / f'product_hunt_{query.replace(" ", "_")}_{timestamp}.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"📁 FILES GENERATED:")
        print(f"   📊 JSON Analysis: {json_file}")
        print(f"   📋 CSV Data: {csv_file}")
        print(f"   📝 Markdown Report: {md_file}")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        print(f"❌ Analysis failed: {str(e)}")
        return None


def generate_google_markdown_report(query, analysis_data, competitors, feedback):
    """Generate a comprehensive markdown report for Google search analysis."""
    
    timestamp = datetime.now().strftime("%B %d, %Y")
    
    report = f"""# 🚀 {query.title()} Market Analysis - Google Search Data

## 🎯 Search Results Summary
- **Search Keywords**: {', '.join(analysis_data['search_keywords'])}
- **Total Competitors Found**: {len(competitors)} solutions
- **Data Source**: Google Search
- **Analysis Date**: {timestamp}
- **Processing Time**: {analysis_data['processing_time_seconds']:.2f} seconds

## 🏆 Top Products by User Base

| Rank | Product | Users | Revenue Est. | Rating | Launch Date |
|------|---------|-------|--------------|--------|-------------|
"""
    
    # Add top competitors table
    for i, comp in enumerate(competitors[:10], 1):
        users = f"{comp.estimated_users:,}" if comp.estimated_users else "N/A"
        revenue = comp.estimated_revenue or "Early stage"
        rating = f"{comp.average_rating}★ ({comp.review_count} reviews)" if comp.average_rating and comp.review_count else "N/A"
        launch_date = comp.launch_date or "N/A"
        
        report += f"| {i} | **{comp.name}** | {users} | {revenue} | {rating} | {launch_date} |\n"
    
    # Founder/CEO information if available
    founders_info = [comp for comp in competitors if comp.founder_ceo]
    if founders_info:
        report += f"""
## 👥 Founder/CEO Information

| Product | Founder/CEO | Launch Date | Company Stage |
|---------|-------------|-------------|---------------|
"""
        for comp in founders_info[:10]:
            stage = "Growth stage" if comp.estimated_users and comp.estimated_users > 50000 else "Early stage"
            report += f"| **{comp.name}** | {comp.founder_ceo} | {comp.launch_date or 'N/A'} | {stage} |\n"
    
    # Review analysis if available
    rated_products = [comp for comp in competitors if comp.average_rating]
    if rated_products:
        report += f"""
## ⭐ Review Analysis

### Highest Rated Products:
"""
        # Sort by rating
        rated_products.sort(key=lambda x: x.average_rating or 0, reverse=True)
        for i, comp in enumerate(rated_products[:5], 1):
            rating = f"{comp.average_rating}★ ({comp.review_count} reviews)" if comp.review_count else f"{comp.average_rating}★"
            report += f"{i}. **{comp.name}** - {rating}\n"
        
        # Add helpful reviews if available
        helpful_reviews = [comp for comp in competitors if comp.most_helpful_review]
        if helpful_reviews:
            report += f"""
### Most Helpful Reviews:

"""
            for comp in helpful_reviews[:5]:
                report += f"""**{comp.name}**:
> "{comp.most_helpful_review}"

"""
    
    # Add feedback analysis if available
    if feedback:
        report += f"""
## 💬 Market Feedback Analysis

"""
        # Group feedback by sentiment
        positive_feedback = [fb for fb in feedback if fb.sentiment == "positive"]
        negative_feedback = [fb for fb in feedback if fb.sentiment == "negative"]
        neutral_feedback = [fb for fb in feedback if fb.sentiment == "neutral"]
        
        if positive_feedback:
            report += f"""### Positive Feedback:
"""
            for fb in positive_feedback[:3]:
                report += f"- {fb.text}\n"
        
        if negative_feedback:
            report += f"""
### Challenges & Concerns:
"""
            for fb in negative_feedback[:3]:
                report += f"- {fb.text}\n"
        
        if neutral_feedback:
            report += f"""
### Market Insights:
"""
            for fb in neutral_feedback[:3]:
                report += f"- {fb.text}\n"
    
    # Market insights
    report += f"""
## 📈 Market Insights

### Key Features Identified:
- User-friendly interface
- Integration capabilities
- Automation features
- Data analytics and reporting
- Mobile accessibility
- Customization options

### Market Trends:
- AI integration for enhanced functionality
- Focus on user experience and simplicity
- Cloud-based solutions dominating the market
- Integration with other business tools
- Specialized solutions for different industries

## 💰 Pricing Models

Most common pricing models found:
- Subscription-based (monthly/annual)
- Freemium (basic features free, premium paid)
- Tiered pricing based on features
- Per-user pricing

## 🎯 Market Opportunities

1. **User Experience**: Simplified, intuitive interfaces
2. **Integration Ecosystem**: Better integration with popular tools
3. **AI-Powered**: Intelligent automation and insights
4. **Industry-Specific**: Solutions tailored for specific industries
5. **Mobile-First**: Solutions designed primarily for mobile use

---
*Data extracted from Google Search using enhanced scraping technology*
*Analysis includes launch dates, founder information, user reviews, and market positioning*
"""
    
    return report


def generate_product_hunt_markdown_report(query, analysis_data, competitors, feedback):
    """Generate a comprehensive markdown report for Product Hunt analysis."""
    
    timestamp = datetime.now().strftime("%B %d, %Y")
    
    report = f"""# 🚀 {query.title()} Market Analysis - Product Hunt Data

## 🎯 Search Results Summary
- **Search Keywords**: {', '.join(analysis_data['search_keywords'])}
- **Total Products Found**: {len(competitors)} solutions
- **Data Source**: Product Hunt
- **Analysis Date**: {timestamp}
- **Processing Time**: {analysis_data['processing_time_seconds']:.2f} seconds

## 🏆 Top Products by User Base

| Rank | Product | Users | Revenue Est. | Rating | Launch Date |
|------|---------|-------|--------------|--------|-------------|
"""
    
    # Add top competitors table
    for i, comp in enumerate(competitors[:10], 1):
        users = f"{comp.estimated_users:,}" if comp.estimated_users else "N/A"
        revenue = comp.estimated_revenue or "Early stage"
        rating = f"{comp.average_rating}★ ({comp.review_count} reviews)" if comp.average_rating and comp.review_count else "N/A"
        launch_date = comp.launch_date or "N/A"
        
        report += f"| {i} | **{comp.name}** | {users} | {revenue} | {rating} | {launch_date} |\n"
    
    # Founder/CEO information if available
    founders_info = [comp for comp in competitors if comp.founder_ceo]
    if founders_info:
        report += f"""
## 👥 Founder/CEO Information

| Product | Founder/CEO | Launch Date | Company Stage |
|---------|-------------|-------------|---------------|
"""
        for comp in founders_info[:10]:
            stage = "Growth stage" if comp.estimated_users and comp.estimated_users > 5000 else "Early stage"
            report += f"| **{comp.name}** | {comp.founder_ceo} | {comp.launch_date or 'N/A'} | {stage} |\n"
    
    # Review analysis if available
    rated_products = [comp for comp in competitors if comp.average_rating]
    if rated_products:
        report += f"""
## ⭐ Review Analysis

### Highest Rated Products:
"""
        # Sort by rating
        rated_products.sort(key=lambda x: x.average_rating or 0, reverse=True)
        for i, comp in enumerate(rated_products[:5], 1):
            rating = f"{comp.average_rating}★ ({comp.review_count} reviews)" if comp.review_count else f"{comp.average_rating}★"
            report += f"{i}. **{comp.name}** - {rating}\n"
        
        # Add helpful reviews if available
        helpful_reviews = [comp for comp in competitors if comp.most_helpful_review]
        if helpful_reviews:
            report += f"""
### Most Helpful Reviews:

"""
            for comp in helpful_reviews[:5]:
                report += f"""**{comp.name}**:
> "{comp.most_helpful_review}"

"""
    
    # Market insights
    report += f"""
## 📈 Market Insights

### Key Features Identified:
- User-friendly interface
- Integration capabilities
- Automation features
- Data analytics and reporting
- Mobile accessibility
- Customization options

### Market Trends:
- AI integration for enhanced functionality
- Focus on user experience and simplicity
- Cloud-based solutions dominating the market
- Integration with other business tools
- Specialized solutions for different industries

## 💰 Pricing Models

Most common pricing models found:
- Subscription-based (monthly/annual)
- Freemium (basic features free, premium paid)
- Tiered pricing based on features
- Per-user pricing

## 🎯 Market Opportunities

1. **User Experience**: Simplified, intuitive interfaces
2. **Integration Ecosystem**: Better integration with popular tools
3. **AI-Powered**: Intelligent automation and insights
4. **Industry-Specific**: Solutions tailored for specific industries
5. **Mobile-First**: Solutions designed primarily for mobile use

---
*Data extracted from Product Hunt using enhanced scraping technology*
*Analysis includes launch dates, founder information, user reviews, and market positioning*
"""
    
    return report


async def test_google_scraper(query: str):
    """Test Google scraper with the given query."""
    print("=" * 80)
    print(f"🚀 GOOGLE SCRAPER TEST: {query}")
    print("=" * 80)
    
    # Initialize the scraper
    scraper = GoogleScraper()
    
    # Generate keywords from query
    keywords = query.split()
    idea_text = f"A {query} platform for businesses"
    
    print(f"📊 Search Keywords: {', '.join(keywords)}")
    print(f"💡 Business Idea: {idea_text}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%B %d, %Y')}")
    print("\nStarting Google scraping...")
    
    try:
        # Execute the scraping
        start_time = datetime.now()
        result = await scraper.scrape(keywords, idea_text)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Scraping completed in {processing_time:.2f} seconds")
        print(f"📊 Status: {result.status}")
        
        if result.error_message:
            print(f"❌ Error: {result.error_message}")
        
        # Process competitor data
        competitors = result.competitors
        
        # Process feedback data
        feedback_data = result.feedback
        
        # Generate analysis data
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'search_keywords': keywords,
            'business_idea': idea_text,
            'total_competitors': len(competitors),
            'total_feedback': len(feedback_data),
            'data_source': 'Google Search',
            'processing_time_seconds': processing_time,
            'scraping_status': result.status.value,
            'competitors': [comp.__dict__ for comp in competitors],
            'feedback': [fb.__dict__ for fb in feedback_data],
            'metadata': result.metadata
        }
        
        # Create output directories
        output_dir = Path('output')
        csv_dir = output_dir / 'csv'
        
        # Ensure directories exist
        output_dir.mkdir(exist_ok=True)
        csv_dir.mkdir(exist_ok=True)
        
        # Save JSON data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = output_dir / f'google_{query.replace(" ", "_")}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        # Save CSV data for competitors
        if competitors:
            csv_file = csv_dir / f'google_{query.replace(" ", "_")}_{timestamp}.csv'
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'name', 'description', 'website', 'estimated_users', 'estimated_revenue', 
                    'pricing_model', 'confidence_score', 'source', 'source_url', 'launch_date',
                    'founder_ceo', 'review_count', 'average_rating', 'most_helpful_review'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for comp in competitors:
                    writer.writerow({
                        'name': comp.name,
                        'description': comp.description or 'N/A',
                        'website': comp.website or 'N/A',
                        'estimated_users': comp.estimated_users or 'N/A',
                        'estimated_revenue': comp.estimated_revenue or 'N/A',
                        'pricing_model': comp.pricing_model or 'N/A',
                        'confidence_score': comp.confidence_score,
                        'source': comp.source,
                        'source_url': comp.source_url or 'N/A',
                        'launch_date': comp.launch_date or 'N/A',
                        'founder_ceo': comp.founder_ceo or 'N/A',
                        'review_count': comp.review_count or 'N/A',
                        'average_rating': comp.average_rating or 'N/A',
                        'most_helpful_review': comp.most_helpful_review or 'N/A'
                    })
        
        # Generate markdown report
        if competitors:
            markdown_report = generate_google_markdown_report(query, analysis_data, competitors, feedback_data)
            md_file = output_dir / f'google_{query.replace(" ", "_")}_{timestamp}.md'
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
        
        # Display results
        print(f"\n📈 ANALYSIS RESULTS")
        print(f"{'='*50}")
        print(f"🏢 Total Competitors Found: {len(competitors)}")
        print(f"💬 Feedback Items: {len(feedback_data)}")
        print(f"⏱️ Processing Time: {processing_time:.2f} seconds")
        
        if result.metadata:
            print(f"🔍 Keywords Searched: {result.metadata.get('keywords_searched', 'N/A')}")
            print(f"📊 Search Queries: {result.metadata.get('search_queries', 'N/A')}")
        
        if competitors:
            print(f"\n🏆 TOP COMPETITORS FROM GOOGLE")
            print(f"{'='*50}")
            for i, comp in enumerate(competitors[:5], 1):
                print(f"{i}. {comp.name}")
                print(f"   📝 Description: {comp.description[:100]}..." if comp.description and len(comp.description) > 100 else f"   📝 Description: {comp.description or 'N/A'}")
                print(f"   🌐 Website: {comp.website or 'N/A'}")
                print(f"   💰 Revenue: {comp.estimated_revenue or 'N/A'}")
                print(f"   🏷️ Pricing: {comp.pricing_model or 'N/A'}")
                print(f"   🔍 Confidence: {comp.confidence_score:.2f}")
                
                # Display reviews/comments if available
                if comp.most_helpful_review:
                    print(f"   💬 Top Review: \"{comp.most_helpful_review[:100]}...\"" if len(comp.most_helpful_review) > 100 else f"   💬 Top Review: \"{comp.most_helpful_review}\"")
                
                # Display ratings if available
                if comp.average_rating:
                    print(f"   ⭐ Rating: {comp.average_rating} ({comp.review_count} reviews)")
                
                # Display launch date and founder if available
                if comp.launch_date:
                    print(f"   🚀 Launched: {comp.launch_date}")
                if comp.founder_ceo:
                    print(f"   👤 Founder/CEO: {comp.founder_ceo}")
                
                print()
        else:
            print("\n❌ No competitors found")
        
        print(f"📁 FILES GENERATED:")
        print(f"   📊 JSON Analysis: {json_file}")
        if competitors:
            print(f"   📋 CSV Data: {csv_file}")
            print(f"   📝 Markdown Report: {md_file}")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        print(f"❌ Analysis failed: {str(e)}")
        return None


async def test_reddit_scraper(query: str):
    """Test Reddit scraper with the given query."""
    print("=" * 80)
    print(f"🚀 REDDIT SCRAPER TEST: {query}")
    print("=" * 80)
    
    # Initialize the scraper
    scraper = RedditScraper()
    
    # Generate keywords from query
    keywords = query.split()
    idea_text = f"A {query} platform for businesses"
    
    print(f"📊 Search Keywords: {', '.join(keywords)}")
    print(f"💡 Business Idea: {idea_text}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%B %d, %Y')}")
    print("\nStarting Reddit scraping...")
    
    try:
        # Execute the scraping
        start_time = datetime.now()
        result = await scraper.scrape(keywords, idea_text)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Scraping completed in {processing_time:.2f} seconds")
        print(f"📊 Status: {result.status}")
        
        if result.error_message:
            print(f"❌ Error: {result.error_message}")
        
        # Process competitor data
        competitors = result.competitors
        
        # Process feedback data
        feedback_data = result.feedback
        
        # Generate analysis data
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'search_keywords': keywords,
            'business_idea': idea_text,
            'total_competitors': len(competitors),
            'total_feedback': len(feedback_data),
            'data_source': 'Reddit',
            'processing_time_seconds': processing_time,
            'scraping_status': result.status.value,
            'competitors': [comp.__dict__ for comp in competitors],
            'feedback': [fb.__dict__ for fb in feedback_data],
            'metadata': result.metadata
        }
        
        # Create output directories
        output_dir = Path('output')
        csv_dir = output_dir / 'csv'
        
        # Ensure directories exist
        output_dir.mkdir(exist_ok=True)
        csv_dir.mkdir(exist_ok=True)
        
        # Save JSON data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = output_dir / f'reddit_{query.replace(" ", "_")}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        # Display results
        print(f"\n📈 ANALYSIS RESULTS")
        print(f"{'='*50}")
        print(f"🏢 Total Competitors Found: {len(competitors)}")
        print(f"💬 Feedback Items: {len(feedback_data)}")
        print(f"⏱️ Processing Time: {processing_time:.2f} seconds")
        
        if result.metadata:
            print(f"🔍 Keywords Searched: {result.metadata.get('keywords_searched', 'N/A')}")
            print(f"📊 Subreddits: {result.metadata.get('subreddits_searched', 'N/A')}")
        
        if competitors:
            print(f"\n🏆 TOP COMPETITORS FROM REDDIT")
            print(f"{'='*50}")
            for i, comp in enumerate(competitors[:5], 1):
                print(f"{i}. {comp.name}")
                print(f"   📝 Description: {comp.description or 'N/A'}")
                print(f"   🔍 Confidence: {comp.confidence_score:.2f}")
                print()
        else:
            print("\n❌ No competitors found")
        
        if feedback_data:
            print(f"\n💬 TOP FEEDBACK FROM REDDIT")
            print(f"{'='*50}")
            for i, fb in enumerate(feedback_data[:3], 1):
                sentiment_emoji = "😃" if fb.sentiment == "positive" else "😐" if fb.sentiment == "neutral" else "😞"
                print(f"{i}. {sentiment_emoji} {fb.text[:100]}...")
                print(f"   Sentiment: {fb.sentiment} ({fb.sentiment_score:.2f})")
                print()
        
        print(f"📁 FILES GENERATED:")
        print(f"   📊 JSON Analysis: {json_file}")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        print(f"❌ Analysis failed: {str(e)}")
        return None


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Test scrapers with specific queries')
    
    parser.add_argument('--product-hunt', action='store_true', help='Test Product Hunt scraper')
    parser.add_argument('--google', action='store_true', help='Test Google scraper')
    parser.add_argument('--reddit', action='store_true', help='Test Reddit scraper')
    parser.add_argument('--all', action='store_true', help='Test all scrapers')
    parser.add_argument('--query', type=str, default='business validation', help='Search query to test')
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    if not (args.product_hunt or args.google or args.reddit or args.all):
        print("Please specify at least one scraper to test (--product-hunt, --google, --reddit, or --all)")
        return
    
    if args.all or args.product_hunt:
        await test_product_hunt_scraper(args.query)
    
    if args.all or args.google:
        await test_google_scraper(args.query)
    
    if args.all or args.reddit:
        await test_reddit_scraper(args.query)


if __name__ == "__main__":
    asyncio.run(main())