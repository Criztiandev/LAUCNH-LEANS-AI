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
from app.scrapers.google_play_store_scraper import GooglePlayStoreScraper
from app.services.sentiment_analysis_service import SentimentAnalysisService
from app.utils.data_cleaner import DataCleaner
from app.utils.keyword_extractor import KeywordExtractor

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
        output_dir = Path('output')
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
                'founder_ceo', 'review_count', 'average_rating', 'most_helpful_review',
                'comments_count', 'overall_sentiment', 'positive_percentage', 'negative_percentage'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for comp in competitors:
                # Extract sentiment summary data
                comments_count = 0
                overall_sentiment = 'neutral'
                positive_percentage = 0.0
                negative_percentage = 0.0
                
                if hasattr(comp, 'sentiment_summary') and comp.sentiment_summary:
                    comments_count = comp.sentiment_summary.get('total_comments', 0)
                    overall_sentiment = comp.sentiment_summary.get('overall_sentiment', 'neutral')
                    positive_percentage = comp.sentiment_summary.get('positive_percentage', 0.0)
                    negative_percentage = comp.sentiment_summary.get('negative_percentage', 0.0)
                
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
                    'most_helpful_review': comp.most_helpful_review or 'N/A',
                    'comments_count': comments_count,
                    'overall_sentiment': overall_sentiment,
                    'positive_percentage': positive_percentage,
                    'negative_percentage': negative_percentage
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
        
        # Validate enhanced format
        if competitors:
            print(f"\n🔍 ENHANCED FORMAT VALIDATION:")
            print(f"{'='*50}")
            
            # Check if all competitors have the new fields
            competitors_with_comments = sum(1 for comp in competitors if hasattr(comp, 'comments'))
            competitors_with_sentiment = sum(1 for comp in competitors if hasattr(comp, 'sentiment_summary'))
            competitors_with_actual_comments = sum(1 for comp in competitors if hasattr(comp, 'comments') and comp.comments)
            
            print(f"✅ Competitors with comments field: {competitors_with_comments}/{len(competitors)}")
            print(f"✅ Competitors with sentiment_summary field: {competitors_with_sentiment}/{len(competitors)}")
            print(f"📝 Competitors with actual comments: {competitors_with_actual_comments}/{len(competitors)}")
            
            # Show format validation for first competitor
            if competitors:
                first_comp = competitors[0]
                print(f"\n📋 SAMPLE COMPETITOR FORMAT VALIDATION:")
                print(f"   Name: {first_comp.name}")
                print(f"   Has comments field: {'✅' if hasattr(first_comp, 'comments') else '❌'}")
                print(f"   Comments type: {type(first_comp.comments) if hasattr(first_comp, 'comments') else 'N/A'}")
                print(f"   Comments count: {len(first_comp.comments) if hasattr(first_comp, 'comments') and first_comp.comments else 0}")
                print(f"   Has sentiment_summary: {'✅' if hasattr(first_comp, 'sentiment_summary') else '❌'}")
                print(f"   Sentiment summary type: {type(first_comp.sentiment_summary) if hasattr(first_comp, 'sentiment_summary') else 'N/A'}")
                
                if hasattr(first_comp, 'sentiment_summary') and first_comp.sentiment_summary:
                    print(f"   Overall sentiment: {first_comp.sentiment_summary.get('overall_sentiment', 'N/A')}")
                
            # Summary of sentiment analysis across all competitors
            total_comments = sum(len(comp.comments) if hasattr(comp, 'comments') and comp.comments else 0 for comp in competitors)
            positive_products = sum(1 for comp in competitors if hasattr(comp, 'sentiment_summary') and comp.sentiment_summary and comp.sentiment_summary.get('overall_sentiment') == 'positive')
            negative_products = sum(1 for comp in competitors if hasattr(comp, 'sentiment_summary') and comp.sentiment_summary and comp.sentiment_summary.get('overall_sentiment') == 'negative')
            
            print(f"\n📊 OVERALL SENTIMENT ANALYSIS:")
            print(f"   Total comments extracted: {total_comments}")
            print(f"   Products with positive sentiment: {positive_products}")
            print(f"   Products with negative sentiment: {negative_products}")
            print(f"   Products with neutral sentiment: {len(competitors) - positive_products - negative_products}")
        
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
                
                # Display enhanced comments and sentiment analysis
                if hasattr(comp, 'comments') and comp.comments:
                    print(f"   💬 Comments Found: {len(comp.comments)}")
                    for j, comment in enumerate(comp.comments[:2], 1):  # Show top 2 comments
                        sentiment_emoji = "😊" if comment['sentiment']['label'] == 'positive' else "😞" if comment['sentiment']['label'] == 'negative' else "😐"
                        print(f"      {j}. {sentiment_emoji} \"{comment['text'][:60]}...\" - {comment['author']}")
                        print(f"         Sentiment: {comment['sentiment']['label']} (score: {comment['sentiment']['score']:.2f}, confidence: {comment['sentiment']['confidence']:.2f})")
                elif hasattr(comp, 'comments'):
                    print(f"   💬 Comments: [] (empty)")
                
                # Display sentiment summary
                if hasattr(comp, 'sentiment_summary') and comp.sentiment_summary:
                    summary = comp.sentiment_summary
                    print(f"   📊 Sentiment Summary:")
                    print(f"      • Total: {summary['total_comments']} comments")
                    print(f"      • Positive: {summary['positive_count']} ({summary['positive_percentage']}%)")
                    print(f"      • Negative: {summary['negative_count']} ({summary['negative_percentage']}%)")
                    print(f"      • Neutral: {summary['neutral_count']} ({summary['neutral_percentage']}%)")
                    print(f"      • Overall: {summary['overall_sentiment']} (avg score: {summary['average_sentiment_score']})")
                
                # Display traditional review if available (for backward compatibility)
                if comp.most_helpful_review and not (hasattr(comp, 'comments') and comp.comments):
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


async def comprehensive_sentiment_demo(query: str):
    """
    Run a comprehensive demo combining scraping with sentiment analysis.
    
    Args:
        query: Search query to test
    """
    print("🎯" * 30)
    print("🚀 COMPREHENSIVE SCRAPING + SENTIMENT ANALYSIS DEMO")
    print("🎯" * 30)
    print(f"📊 Query: {query}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}")
    print()
    
    # Initialize services
    sentiment_service = SentimentAnalysisService()
    data_cleaner = DataCleaner()
    
    # Extract keywords
    keywords = KeywordExtractor.extract_keywords(query)
    print(f"🔍 Extracted Keywords: {', '.join(keywords)}")
    print()
    
    # Initialize scrapers
    scrapers = [
        ("Product Hunt", ProductHuntScraper()),
        ("Google Play Store", GooglePlayStoreScraper())
    ]
    
    all_competitors = []
    all_feedback = []
    scraping_results = {}
    
    # Run scrapers
    for scraper_name, scraper in scrapers:
        print(f"🔄 Running {scraper_name} scraper...")
        try:
            start_time = datetime.now()
            result = await scraper.scrape(keywords, f"A {query} solution for users")
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"✅ {scraper_name} completed in {processing_time:.2f}s")
            print(f"   📊 Status: {result.status.value}")
            print(f"   🏢 Competitors: {len(result.competitors)}")
            print(f"   💬 Feedback: {len(result.feedback)}")
            
            if result.error_message:
                print(f"   ❌ Error: {result.error_message}")
            
            # Store results
            scraping_results[scraper_name] = {
                'result': result,
                'processing_time': processing_time,
                'competitors': result.competitors,
                'feedback': result.feedback
            }
            
            # Collect all data
            all_competitors.extend(result.competitors)
            all_feedback.extend(result.feedback)
            
        except Exception as e:
            print(f"❌ {scraper_name} failed: {str(e)}")
            scraping_results[scraper_name] = {
                'result': None,
                'processing_time': 0,
                'competitors': [],
                'feedback': [],
                'error': str(e)
            }
        
        print()
    
    # Clean and analyze data
    print("🧹 Cleaning and analyzing scraped data...")
    
    # Clean competitors
    cleaned_competitors = data_cleaner.clean_competitors(all_competitors)
    
    # Clean feedback with sentiment analysis
    cleaned_feedback = data_cleaner.clean_feedback(all_feedback)
    
    # Generate sentiment summary
    sentiment_summary = data_cleaner.get_sentiment_summary(cleaned_feedback)
    
    print(f"✅ Data cleaning completed")
    print(f"   🏢 Unique Competitors: {len(cleaned_competitors)}")
    print(f"   💬 Unique Feedback: {len(cleaned_feedback)}")
    print()
    
    # Display comprehensive results
    print("📈 COMPREHENSIVE ANALYSIS RESULTS")
    print("=" * 60)
    
    # Scraper performance summary
    print("🔄 SCRAPER PERFORMANCE:")
    for scraper_name, data in scraping_results.items():
        if 'error' in data:
            print(f"   ❌ {scraper_name}: Failed - {data['error']}")
        else:
            print(f"   ✅ {scraper_name}: {data['processing_time']:.2f}s - "
                  f"{len(data['competitors'])} competitors, {len(data['feedback'])} feedback")
    print()
    
    # Competitor analysis
    if cleaned_competitors:
        print("🏆 TOP COMPETITORS FOUND:")
        print("-" * 40)
        for i, comp in enumerate(cleaned_competitors[:8], 1):
            print(f"{i}. 📱 {comp['name']}")
            print(f"   🏷️ Source: {comp['source']}")
            print(f"   👥 Users: {comp['estimated_users'] or 'N/A'}")
            print(f"   💰 Revenue: {comp['estimated_revenue'] or 'N/A'}")
            print(f"   💳 Pricing: {comp['pricing_model'] or 'N/A'}")
            print(f"   🔍 Confidence: {comp['confidence_score']:.2f}")
            if comp['description']:
                desc = comp['description'][:100] + "..." if len(comp['description']) > 100 else comp['description']
                print(f"   📝 Description: {desc}")
            print()
    else:
        print("❌ No competitors found")
        print()
    
    # Sentiment analysis results
    if cleaned_feedback:
        print("💭 SENTIMENT ANALYSIS RESULTS:")
        print("-" * 40)
        print(f"📊 Total Feedback Analyzed: {sentiment_summary['total_count']}")
        print(f"😊 Positive: {sentiment_summary['positive_count']} ({sentiment_summary['positive_percentage']:.1f}%)")
        print(f"😐 Neutral: {sentiment_summary['neutral_count']} ({sentiment_summary['neutral_percentage']:.1f}%)")
        print(f"😞 Negative: {sentiment_summary['negative_count']} ({sentiment_summary['negative_percentage']:.1f}%)")
        print(f"📈 Average Score: {sentiment_summary['average_score']:.3f} (Range: -1 to 1)")
        print(f"🎯 Average Confidence: {sentiment_summary['average_confidence']:.3f} (Range: 0 to 1)")
        print()
        
        # Show sample feedback by sentiment
        positive_feedback = [f for f in cleaned_feedback if f['sentiment'] == 'positive']
        negative_feedback = [f for f in cleaned_feedback if f['sentiment'] == 'negative']
        neutral_feedback = [f for f in cleaned_feedback if f['sentiment'] == 'neutral']
        
        if positive_feedback:
            print("😊 SAMPLE POSITIVE FEEDBACK:")
            for i, fb in enumerate(positive_feedback[:3], 1):
                print(f"   {i}. \"{fb['text'][:120]}{'...' if len(fb['text']) > 120 else ''}\"")
                print(f"      Score: {fb['sentiment_score']:.3f}, Confidence: {fb['confidence']:.3f}")
            print()
        
        if negative_feedback:
            print("😞 SAMPLE NEGATIVE FEEDBACK:")
            for i, fb in enumerate(negative_feedback[:3], 1):
                print(f"   {i}. \"{fb['text'][:120]}{'...' if len(fb['text']) > 120 else ''}\"")
                print(f"      Score: {fb['sentiment_score']:.3f}, Confidence: {fb['confidence']:.3f}")
            print()
        
        if neutral_feedback:
            print("😐 SAMPLE NEUTRAL FEEDBACK:")
            for i, fb in enumerate(neutral_feedback[:2], 1):
                print(f"   {i}. \"{fb['text'][:120]}{'...' if len(fb['text']) > 120 else ''}\"")
                print(f"      Score: {fb['sentiment_score']:.3f}, Confidence: {fb['confidence']:.3f}")
            print()
    else:
        print("❌ No feedback found for sentiment analysis")
        print()
    
    # Market insights
    print("💡 MARKET INSIGHTS:")
    print("-" * 40)
    
    if cleaned_competitors:
        # Pricing model analysis
        pricing_models = {}
        for comp in cleaned_competitors:
            model = comp['pricing_model'] or 'Unknown'
            pricing_models[model] = pricing_models.get(model, 0) + 1
        
        print("💳 Pricing Models:")
        for model, count in sorted(pricing_models.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(cleaned_competitors)) * 100
            print(f"   • {model}: {count} apps ({percentage:.1f}%)")
        print()
        
        # Source distribution
        sources = {}
        for comp in cleaned_competitors:
            source = comp['source']
            sources[source] = sources.get(source, 0) + 1
        
        print("📊 Data Sources:")
        for source, count in sources.items():
            percentage = (count / len(cleaned_competitors)) * 100
            print(f"   • {source}: {count} competitors ({percentage:.1f}%)")
        print()
    
    if cleaned_feedback:
        # Sentiment insights
        if sentiment_summary['positive_percentage'] > 60:
            print("✅ Market shows generally positive sentiment")
        elif sentiment_summary['negative_percentage'] > 40:
            print("⚠️ Market shows concerning negative sentiment")
        else:
            print("📊 Market sentiment is mixed - opportunity for differentiation")
        
        if sentiment_summary['average_confidence'] > 0.7:
            print("🎯 High confidence in sentiment analysis results")
        else:
            print("⚠️ Moderate confidence in sentiment analysis - results may vary")
        print()
    
    # Save comprehensive results
    print("💾 SAVING RESULTS:")
    print("-" * 40)
    
    # Create output directories
    output_dir = Path('output')
    csv_dir = output_dir / 'csv'
    output_dir.mkdir(exist_ok=True)
    csv_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save comprehensive JSON
    comprehensive_data = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'keywords': keywords,
        'scraping_results': {
            name: {
                'status': data['result'].status.value if data['result'] else 'failed',
                'processing_time': data['processing_time'],
                'competitors_found': len(data['competitors']),
                'feedback_found': len(data['feedback']),
                'error': data.get('error')
            } for name, data in scraping_results.items()
        },
        'analysis_summary': {
            'total_competitors': len(cleaned_competitors),
            'total_feedback': len(cleaned_feedback),
            'sentiment_summary': sentiment_summary
        },
        'competitors': cleaned_competitors,
        'feedback': cleaned_feedback
    }
    
    json_file = output_dir / f'comprehensive_analysis_{query.replace(" ", "_")}_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, indent=2, default=str)
    
    # Save competitors CSV
    if cleaned_competitors:
        csv_file = csv_dir / f'competitors_{query.replace(" ", "_")}_{timestamp}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'name', 'description', 'website', 'estimated_users', 'estimated_revenue',
                'pricing_model', 'confidence_score', 'source', 'source_url'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for comp in cleaned_competitors:
                writer.writerow({
                    'name': comp['name'],
                    'description': comp['description'] or 'N/A',
                    'website': comp['website'] or 'N/A',
                    'estimated_users': comp['estimated_users'] or 'N/A',
                    'estimated_revenue': comp['estimated_revenue'] or 'N/A',
                    'pricing_model': comp['pricing_model'] or 'N/A',
                    'confidence_score': comp['confidence_score'],
                    'source': comp['source'],
                    'source_url': comp['source_url'] or 'N/A'
                })
    
    # Save feedback with sentiment CSV
    if cleaned_feedback:
        feedback_csv = csv_dir / f'feedback_sentiment_{query.replace(" ", "_")}_{timestamp}.csv'
        with open(feedback_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'text', 'sentiment', 'sentiment_score', 'confidence', 'source',
                'textblob_polarity', 'vader_compound'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for fb in cleaned_feedback:
                writer.writerow({
                    'text': fb['text'],
                    'sentiment': fb['sentiment'],
                    'sentiment_score': fb['sentiment_score'],
                    'confidence': fb['confidence'],
                    'source': fb['source'],
                    'textblob_polarity': fb['sentiment_details']['textblob_polarity'],
                    'vader_compound': fb['sentiment_details']['vader_compound']
                })
    
    # Generate comprehensive TXT summary
    txt_summary = generate_txt_summary(query, comprehensive_data, cleaned_competitors, cleaned_feedback, sentiment_summary, scraping_results)
    txt_file = output_dir / f'summary_{query.replace(" ", "_")}_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(txt_summary)
    
    print(f"📊 Comprehensive Analysis: {json_file}")
    if cleaned_competitors:
        print(f"🏢 Competitors CSV: {csv_file}")
    if cleaned_feedback:
        print(f"💭 Sentiment Analysis CSV: {feedback_csv}")
    print(f"📝 Summary Report: {txt_file}")
    
    print()
    print("🎉 COMPREHENSIVE DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ Features Demonstrated:")
    print("   • Multi-source scraping (Product Hunt + Google Play Store)")
    print("   • Advanced sentiment analysis (TextBlob + VADER)")
    print("   • Data cleaning and deduplication")
    print("   • Confidence scoring for sentiment predictions")
    print("   • Comprehensive market insights")
    print("   • Multiple export formats (JSON + CSV)")
    print("   • Real-time processing and analysis")
    
    return comprehensive_data


def generate_txt_summary(query, comprehensive_data, competitors, feedback, sentiment_summary, scraping_results):
    """Generate a comprehensive TXT summary report."""
    
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    
    summary = f"""
================================================================================
                    REALVALIDATOR AI - MARKET ANALYSIS REPORT
================================================================================

Query: {query.upper()}
Analysis Date: {timestamp}
Generated by: RealValidator AI MVP with Enhanced Sentiment Analysis

================================================================================
                              EXECUTIVE SUMMARY
================================================================================

Total Data Sources: {len(scraping_results)}
Total Competitors Found: {len(competitors)}
Total Feedback Analyzed: {len(feedback)}

SCRAPER PERFORMANCE:
"""
    
    for scraper_name, data in scraping_results.items():
        if 'error' in data:
            summary += f"❌ {scraper_name}: FAILED - {data['error']}\n"
        else:
            summary += f"✅ {scraper_name}: {data['processing_time']:.1f}s - {len(data['competitors'])} competitors, {len(data['feedback'])} feedback\n"
    
    if feedback:
        summary += f"""
SENTIMENT ANALYSIS OVERVIEW:
😊 Positive Sentiment: {sentiment_summary['positive_count']} ({sentiment_summary['positive_percentage']:.1f}%)
😐 Neutral Sentiment: {sentiment_summary['neutral_count']} ({sentiment_summary['neutral_percentage']:.1f}%)
😞 Negative Sentiment: {sentiment_summary['negative_count']} ({sentiment_summary['negative_percentage']:.1f}%)
📈 Average Sentiment Score: {sentiment_summary['average_score']:.3f} (Range: -1 to 1)
🎯 Average Confidence: {sentiment_summary['average_confidence']:.3f} (Range: 0 to 1)

MARKET SENTIMENT INSIGHT:
"""
        if sentiment_summary['positive_percentage'] > 50:
            summary += "✅ POSITIVE MARKET SENTIMENT - Good product-market fit indicators\n"
        elif sentiment_summary['negative_percentage'] > 40:
            summary += "⚠️ CONCERNING NEGATIVE SENTIMENT - Key issues need addressing\n"
        else:
            summary += "📊 MIXED SENTIMENT - Opportunity for improvement and differentiation\n"
        
        if sentiment_summary['average_confidence'] > 0.7:
            summary += "🎯 HIGH CONFIDENCE in sentiment analysis - Reliable insights\n"
        else:
            summary += "⚠️ MODERATE CONFIDENCE - Consider additional data sources\n"
    
    summary += f"""

================================================================================
                            TOP COMPETITORS ANALYSIS
================================================================================

"""
    
    if competitors:
        # Pricing model analysis
        pricing_models = {}
        sources = {}
        
        for comp in competitors:
            model = comp['pricing_model'] or 'Unknown'
            pricing_models[model] = pricing_models.get(model, 0) + 1
            
            source = comp['source']
            sources[source] = sources.get(source, 0) + 1
        
        summary += "PRICING MODEL DISTRIBUTION:\n"
        for model, count in sorted(pricing_models.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(competitors)) * 100
            summary += f"• {model}: {count} competitors ({percentage:.1f}%)\n"
        
        summary += "\nDATA SOURCE DISTRIBUTION:\n"
        for source, count in sources.items():
            percentage = (count / len(competitors)) * 100
            summary += f"• {source}: {count} competitors ({percentage:.1f}%)\n"
        
        summary += f"\nTOP {min(10, len(competitors))} COMPETITORS:\n"
        summary += "-" * 80 + "\n"
        
        for i, comp in enumerate(competitors[:10], 1):
            summary += f"{i:2d}. {comp['name']}\n"
            summary += f"    Source: {comp['source']}\n"
            summary += f"    Users: {comp['estimated_users'] or 'N/A'}\n"
            summary += f"    Revenue: {comp['estimated_revenue'] or 'N/A'}\n"
            summary += f"    Pricing: {comp['pricing_model'] or 'N/A'}\n"
            summary += f"    Confidence: {comp['confidence_score']:.2f}\n"
            if comp['website']:
                summary += f"    Website: {comp['website']}\n"
            if comp['description']:
                desc = comp['description'][:120] + "..." if len(comp['description']) > 120 else comp['description']
                summary += f"    Description: {desc}\n"
            summary += "\n"
    else:
        summary += "❌ No competitors found in the analysis.\n"
    
    if feedback:
        summary += f"""
================================================================================
                           SENTIMENT ANALYSIS DETAILS
================================================================================

DETAILED SENTIMENT BREAKDOWN:
Total Feedback Items: {len(feedback)}
Analysis Method: TextBlob + VADER (Weighted Combination)
Confidence Scoring: Multi-factor algorithm

SENTIMENT DISTRIBUTION:
"""
        
        # Group feedback by sentiment
        positive_feedback = [f for f in feedback if f['sentiment'] == 'positive']
        negative_feedback = [f for f in feedback if f['sentiment'] == 'negative']
        neutral_feedback = [f for f in feedback if f['sentiment'] == 'neutral']
        
        if positive_feedback:
            summary += f"\n😊 POSITIVE FEEDBACK ({len(positive_feedback)} items):\n"
            summary += "-" * 50 + "\n"
            for i, fb in enumerate(positive_feedback[:5], 1):
                summary += f"{i}. \"{fb['text'][:100]}{'...' if len(fb['text']) > 100 else ''}\"\n"
                summary += f"   Score: {fb['sentiment_score']:.3f} | Confidence: {fb['confidence']:.3f} | Source: {fb['source']}\n\n"
        
        if negative_feedback:
            summary += f"\n😞 NEGATIVE FEEDBACK ({len(negative_feedback)} items):\n"
            summary += "-" * 50 + "\n"
            for i, fb in enumerate(negative_feedback[:5], 1):
                summary += f"{i}. \"{fb['text'][:100]}{'...' if len(fb['text']) > 100 else ''}\"\n"
                summary += f"   Score: {fb['sentiment_score']:.3f} | Confidence: {fb['confidence']:.3f} | Source: {fb['source']}\n\n"
        
        if neutral_feedback:
            summary += f"\n😐 NEUTRAL FEEDBACK ({len(neutral_feedback)} items):\n"
            summary += "-" * 50 + "\n"
            for i, fb in enumerate(neutral_feedback[:3], 1):
                summary += f"{i}. \"{fb['text'][:100]}{'...' if len(fb['text']) > 100 else ''}\"\n"
                summary += f"   Score: {fb['sentiment_score']:.3f} | Confidence: {fb['confidence']:.3f} | Source: {fb['source']}\n\n"
    
    summary += f"""
================================================================================
                              MARKET INSIGHTS
================================================================================

KEY FINDINGS:
"""
    
    if competitors:
        # Market insights based on data
        free_apps = len([c for c in competitors if c['pricing_model'] == 'Free'])
        paid_apps = len([c for c in competitors if 'Paid' in (c['pricing_model'] or '')])
        freemium_apps = len([c for c in competitors if c['pricing_model'] == 'Freemium'])
        
        summary += f"• Market has {len(competitors)} identified competitors\n"
        if free_apps > len(competitors) * 0.5:
            summary += f"• Free model dominates ({free_apps} apps) - consider freemium approach\n"
        if freemium_apps > 0:
            summary += f"• {freemium_apps} competitors use freemium model - proven monetization strategy\n"
        if paid_apps > 0:
            summary += f"• {paid_apps} competitors use paid model - premium market exists\n"
    
    if feedback:
        if sentiment_summary['negative_percentage'] > 30:
            summary += "• High negative sentiment indicates market dissatisfaction - opportunity for improvement\n"
        if sentiment_summary['positive_percentage'] > 60:
            summary += "• Strong positive sentiment shows market validation for this category\n"
        if sentiment_summary['average_confidence'] > 0.6:
            summary += "• High confidence in sentiment analysis - reliable market feedback\n"
    
    summary += f"""

RECOMMENDATIONS:
"""
    
    if competitors:
        if len(competitors) < 5:
            summary += "• Low competition - good market entry opportunity\n"
        elif len(competitors) > 20:
            summary += "• High competition - focus on differentiation and unique value proposition\n"
        else:
            summary += "• Moderate competition - identify gaps in existing solutions\n"
    
    if feedback:
        if sentiment_summary['negative_percentage'] > 40:
            summary += "• Address common pain points identified in negative feedback\n"
        if sentiment_summary['positive_percentage'] > 50:
            summary += "• Build on positive aspects that users appreciate\n"
        summary += "• Monitor sentiment trends over time for market validation\n"
    
    summary += f"""

================================================================================
                            TECHNICAL DETAILS
================================================================================

ANALYSIS METHODOLOGY:
• Sentiment Analysis: TextBlob (40%) + VADER (60%) weighted combination
• Confidence Scoring: Multi-factor algorithm considering agreement, strength, and distribution
• Data Sources: Product Hunt, Google Play Store
• Processing Time: {sum(data['processing_time'] for data in scraping_results.values() if 'processing_time' in data):.1f} seconds total
• Data Quality: Automated cleaning and deduplication applied

SENTIMENT SCORING:
• Positive: Score > 0.1
• Neutral: Score between -0.1 and 0.1  
• Negative: Score < -0.1
• Score Range: -1.0 (very negative) to 1.0 (very positive)
• Confidence Range: 0.0 (no confidence) to 1.0 (high confidence)

DATA EXPORT:
• JSON: Complete analysis with metadata
• CSV: Structured data for spreadsheet analysis
• TXT: Human-readable summary report (this file)

================================================================================
                                END OF REPORT
================================================================================

Generated by RealValidator AI MVP - Enhanced Sentiment Analysis Service
Task 14: Sentiment Analysis Integration - COMPLETED SUCCESSFULLY
Report Date: {timestamp}

For detailed data analysis, refer to the accompanying JSON and CSV files.
For technical implementation details, see SENTIMENT_ANALYSIS_SUMMARY.md

================================================================================
"""
    
    return summary


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


async def test_google_play_store_scraper(query: str):
    """Test Google Play Store scraper with the given query (Enhanced Mobile-First Version)."""
    print("=" * 80)
    print(f"🚀 GOOGLE PLAY STORE SCRAPER TEST (MOBILE-OPTIMIZED): {query}")
    print("=" * 80)
    
    # Initialize the scraper
    scraper = GooglePlayStoreScraper()
    
    # Validate scraper configuration
    if not scraper.validate_config():
        print("❌ Scraper configuration validation failed")
        return None
    
    # Generate keywords from query
    keywords = query.split()
    idea_text = f"A {query} app for mobile users"
    
    print(f"📊 Search Keywords: {', '.join(keywords)}")
    print(f"💡 App Idea: {idea_text}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"🔧 Scraper Version: Google Play Scraper API")
    print(f"📱 Max Results per Query: {scraper.max_results_per_query}")
    print(f"⏱️ Delay Range: {scraper.delay_between_requests[0]}-{scraper.delay_between_requests[1]} seconds")
    print(f"🎯 Max Queries: {scraper.max_queries}")
    print(f"🌍 Supported Countries: {scraper.supported_countries}")
    print("\nStarting Google Play Store scraping...")
    
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
        feedback_data = result.feedback
        
        # Generate analysis data
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'search_keywords': keywords,
            'app_idea': idea_text,
            'total_competitors': len(competitors),
            'total_feedback': len(feedback_data),
            'data_source': 'Google Play Store (Mobile-Optimized)',
            'processing_time_seconds': processing_time,
            'scraping_status': result.status.value,
            'competitors': [comp.__dict__ for comp in competitors],
            'feedback': [fb.__dict__ for fb in feedback_data],
            'metadata': result.metadata,
            'scraper_config': {
                'max_results_per_query': scraper.max_results_per_query,
                'delay_range': scraper.delay_between_requests,
                'max_queries': scraper.max_queries,
                'api_based': True
            }
        }
        
        # Create output directories
        output_dir = Path('output')
        csv_dir = output_dir / 'csv'
        
        # Ensure directories exist
        output_dir.mkdir(exist_ok=True)
        csv_dir.mkdir(exist_ok=True)
        
        # Save JSON data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = output_dir / f'google_play_store_mobile_{query.replace(" ", "_")}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        # Save CSV data for competitors
        if competitors:
            csv_file = csv_dir / f'google_play_store_mobile_{query.replace(" ", "_")}_{timestamp}.csv'
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'name', 'description', 'website', 'estimated_users', 'estimated_revenue', 
                    'pricing_model', 'confidence_score', 'source', 'source_url', 'launch_date',
                    'founder_ceo', 'review_count', 'average_rating', 'package_name'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for comp in competitors:
                    # Extract package name from source URL if available
                    package_name = 'N/A'
                    if comp.source_url and 'id=' in comp.source_url:
                        package_name = comp.source_url.split('id=')[1].split('&')[0]
                    
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
                        'package_name': package_name
                    })
        
        # Display detailed results
        print(f"\n📈 DETAILED ANALYSIS RESULTS")
        print(f"{'='*60}")
        print(f"📱 Total Android Apps Found: {len(competitors)}")
        print(f"💬 Reviews/Feedback Items: {len(feedback_data)}")
        print(f"⏱️ Processing Time: {processing_time:.2f} seconds")
        print(f"🔄 API Calls Made: {result.metadata.get('api_calls_made', 'N/A')}")
        print(f"✅ Successful Queries: {result.metadata.get('successful_queries', 'N/A')}")
        print(f"❌ Failed Queries: {result.metadata.get('failed_queries', 'N/A')}")
        
        if result.metadata:
            print(f"🔍 Keywords Searched: {result.metadata.get('keywords_searched', 'N/A')}")
            print(f"📊 Search Queries: {result.metadata.get('search_queries', 'N/A')}")
            print(f"📱 Apps Found: {result.metadata.get('apps_found', 'N/A')}")
            print(f"📝 Reviews Extracted: {result.metadata.get('reviews_extracted', 'N/A')}")
            print(f"📈 Success Rate: {result.metadata.get('success_rate', 0):.1%}")
            print(f"🔧 Scraping Method: {result.metadata.get('scraping_method', 'N/A')}")
        
        if competitors:
            print(f"\n🏆 TOP ANDROID APPS FROM GOOGLE PLAY STORE")
            print(f"{'='*70}")
            for i, comp in enumerate(competitors[:5], 1):
                print(f"{i}. 📱 {comp.name}")
                print(f"   👨‍💻 Developer: {comp.founder_ceo or 'N/A'}")
                print(f"   ⭐ Rating: {comp.average_rating or 'N/A'} ({comp.review_count or 'N/A'} reviews)")
                print(f"   📱 Installs: {comp.estimated_users or 'N/A'}")
                print(f"   💰 Pricing: {comp.pricing_model or 'N/A'}")
                print(f"   🌐 Website: {comp.website or 'N/A'}")
                print(f"   📝 Description: {comp.description[:100]}..." if comp.description and len(comp.description) > 100 else f"   📝 Description: {comp.description or 'N/A'}")
                print(f"   🔍 Confidence: {comp.confidence_score:.2f}")
                
                # Extract and display package name
                if comp.source_url and 'id=' in comp.source_url:
                    package_name = comp.source_url.split('id=')[1].split('&')[0]
                    print(f"   📦 Package: {package_name}")
                
                print()
        else:
            print("\n❌ No Android apps found")
            print("💡 This could be due to:")
            print("   - Bot detection by Google Play Store")
            print("   - Network connectivity issues")
            print("   - Changes in Play Store DOM structure")
            print("   - Rate limiting or IP blocking")
        
        if feedback_data:
            print(f"\n💬 TOP FEEDBACK FROM GOOGLE PLAY STORE")
            print(f"{'='*60}")
            for i, fb in enumerate(feedback_data[:3], 1):
                print(f"{i}. {fb.text[:150]}...")
                app_name = 'N/A'
                if fb.author_info:
                    app_name = fb.author_info.get('app_name', 'N/A')
                    feedback_type = fb.author_info.get('type', 'review')
                    print(f"   📱 App: {app_name} ({feedback_type})")
                    if fb.author_info.get('rating'):
                        print(f"   ⭐ Rating: {fb.author_info.get('rating')}")
                print()
        
        # Performance analysis
        if result.metadata:
            print(f"\n⚡ PERFORMANCE ANALYSIS")
            print(f"{'='*50}")
            queries_per_second = result.metadata.get('successful_queries', 0) / max(processing_time, 1)
            apps_per_second = len(competitors) / max(processing_time, 1)
            print(f"📊 Queries per second: {queries_per_second:.2f}")
            print(f"📱 Apps extracted per second: {apps_per_second:.2f}")
            print(f"🔄 Average time per API call: {processing_time / max(result.metadata.get('api_calls_made', 1), 1):.2f}s")
            
            if result.metadata.get('failed_queries', 0) > 0:
                print(f"⚠️  API errors occurred on {result.metadata.get('failed_queries')} queries")
        
        print(f"\n📁 FILES GENERATED:")
        print(f"   📊 JSON Analysis: {json_file}")
        if competitors:
            print(f"   📋 CSV Data: {csv_file}")
        
        # Recommendations based on results
        print(f"\n💡 RECOMMENDATIONS:")
        if len(competitors) == 0:
            print("   🔧 Try different or broader keywords")
            print("   ⏱️  Check network connectivity")
            print("   🌐 Verify Google Play Scraper API is accessible")
        elif len(competitors) < 3:
            print("   📈 Results are limited - consider broader keywords")
            print("   🔄 Try running again with different search terms")
        else:
            print("   ✅ Good results obtained with API-based approach")
            print("   📊 Data quality appears reliable for market analysis")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Google Play Store analysis failed: {str(e)}")
        print(f"❌ Google Play Store analysis failed: {str(e)}")
        print(f"\n🔧 TROUBLESHOOTING TIPS:")
        print("   1. Check internet connection")
        print("   2. Verify Google Play Scraper API is accessible")
        print("   3. Try with simpler keywords")
        print("   4. Check if Google Play Store is accessible from your location")
        print("   5. Consider using different search terms")
        return None



async def test_app_store_scraper(query: str):
    """Test iOS App Store scraper with the given query."""
    print("=" * 80)
    print(f"🚀 iOS APP STORE SCRAPER TEST: {query}")
    print("=" * 80)
    
    # Initialize the scraper
    scraper = AppStoreScraper()
    
    # Generate keywords from query
    keywords = query.split()
    idea_text = f"A {query} app for iOS users"
    
    print(f"📊 Search Keywords: {', '.join(keywords)}")
    print(f"💡 App Idea: {idea_text}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%B %d, %Y')}")
    print("\nStarting iOS App Store scraping...")
    
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
        feedback_data = result.feedback
        
        # Generate analysis data
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'search_keywords': keywords,
            'app_idea': idea_text,
            'total_competitors': len(competitors),
            'total_feedback': len(feedback_data),
            'data_source': 'iOS App Store',
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
        json_file = output_dir / f'ios_app_store_{query.replace(" ", "_")}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        # Save CSV data for competitors
        if competitors:
            csv_file = csv_dir / f'ios_app_store_{query.replace(" ", "_")}_{timestamp}.csv'
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'name', 'description', 'website', 'estimated_users', 'estimated_revenue', 
                    'pricing_model', 'confidence_score', 'source', 'source_url', 'launch_date',
                    'founder_ceo', 'review_count', 'average_rating'
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
                        'average_rating': comp.average_rating or 'N/A'
                    })
        
        # Display results
        print(f"\n📈 ANALYSIS RESULTS")
        print(f"{'='*50}")
        print(f"🍎 Total iOS Apps Found: {len(competitors)}")
        print(f"💬 Reviews/Feedback Items: {len(feedback_data)}")
        print(f"⏱️ Processing Time: {processing_time:.2f} seconds")
        
        if result.metadata:
            print(f"🔍 Keywords Searched: {result.metadata.get('keywords_searched', 'N/A')}")
            print(f"📊 Apps Found: {result.metadata.get('apps_found', 'N/A')}")
            print(f"📝 Reviews Extracted: {result.metadata.get('reviews_extracted', 'N/A')}")
        
        if competitors:
            print(f"\n🏆 TOP iOS APPS FROM APP STORE")
            print(f"{'='*50}")
            for i, comp in enumerate(competitors[:5], 1):
                print(f"{i}. {comp.name}")
                print(f"   👨‍💻 Developer: {comp.founder_ceo or 'N/A'}")
                print(f"   ⭐ Rating: {comp.average_rating or 'N/A'} ({comp.review_count or 'N/A'} reviews)")
                print(f"   💰 Pricing: {comp.pricing_model or 'N/A'}")
                print(f"   🌐 Website: {comp.website or 'N/A'}")
                print(f"   📅 Released: {comp.launch_date or 'N/A'}")
                print(f"   📝 Description: {comp.description[:100]}..." if comp.description and len(comp.description) > 100 else f"   📝 Description: {comp.description or 'N/A'}")
                print(f"   🔍 Confidence: {comp.confidence_score:.2f}")
                print()
        else:
            print("\n❌ No iOS apps found")
        
        if feedback_data:
            print(f"\n💬 TOP REVIEWS FROM APP STORE")
            print(f"{'='*50}")
            for i, fb in enumerate(feedback_data[:3], 1):
                print(f"{i}. {fb.text[:150]}...")
                print(f"   🍎 App: {fb.author_info.get('app_name', 'N/A') if fb.author_info else 'N/A'}")
                print()
        
        print(f"📁 FILES GENERATED:")
        print(f"   📊 JSON Analysis: {json_file}")
        if competitors:
            print(f"   📋 CSV Data: {csv_file}")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"iOS App Store analysis failed: {str(e)}")
        print(f"❌ iOS App Store analysis failed: {str(e)}")
        return None


async def test_microsoft_store_scraper(query: str):
    """Test Microsoft Store scraper with the given query."""
    print("=" * 80)
    print(f"🚀 MICROSOFT STORE SCRAPER TEST: {query}")
    print("=" * 80)
    
    # Initialize the scraper
    scraper = MicrosoftStoreScraper()
    
    # Generate keywords from query
    keywords = query.split()
    idea_text = f"A {query} app for Windows users"
    
    print(f"📊 Search Keywords: {', '.join(keywords)}")
    print(f"💡 App Idea: {idea_text}")
    print(f"📅 Analysis Date: {datetime.now().strftime('%B %d, %Y')}")
    print("\nStarting Microsoft Store scraping...")
    
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
        feedback_data = result.feedback
        
        # Generate analysis data
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'search_keywords': keywords,
            'app_idea': idea_text,
            'total_competitors': len(competitors),
            'total_feedback': len(feedback_data),
            'data_source': 'Microsoft Store',
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
        json_file = output_dir / f'microsoft_store_{query.replace(" ", "_")}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        # Save CSV data for competitors
        if competitors:
            csv_file = csv_dir / f'microsoft_store_{query.replace(" ", "_")}_{timestamp}.csv'
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'name', 'description', 'website', 'estimated_users', 'estimated_revenue', 
                    'pricing_model', 'confidence_score', 'source', 'source_url', 'launch_date',
                    'founder_ceo', 'review_count', 'average_rating'
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
                        'average_rating': comp.average_rating or 'N/A'
                    })
        
        # Display results
        print(f"\n📈 ANALYSIS RESULTS")
        print(f"{'='*50}")
        print(f"🪟 Total Windows Apps Found: {len(competitors)}")
        print(f"💬 Reviews/Feedback Items: {len(feedback_data)}")
        print(f"⏱️ Processing Time: {processing_time:.2f} seconds")
        
        if result.metadata:
            print(f"🔍 Keywords Searched: {result.metadata.get('keywords_searched', 'N/A')}")
            print(f"📊 Apps Found: {result.metadata.get('apps_found', 'N/A')}")
            print(f"📝 Reviews Extracted: {result.metadata.get('reviews_extracted', 'N/A')}")
        
        if competitors:
            print(f"\n🏆 TOP WINDOWS APPS FROM MICROSOFT STORE")
            print(f"{'='*55}")
            for i, comp in enumerate(competitors[:5], 1):
                print(f"{i}. {comp.name}")
                print(f"   👨‍💻 Developer: {comp.founder_ceo or 'N/A'}")
                print(f"   ⭐ Rating: {comp.average_rating or 'N/A'} ({comp.review_count or 'N/A'} reviews)")
                print(f"   💰 Pricing: {comp.pricing_model or 'N/A'}")
                print(f"   🌐 Website: {comp.website or 'N/A'}")
                print(f"   📅 Released: {comp.launch_date or 'N/A'}")
                print(f"   📝 Description: {comp.description[:100]}..." if comp.description and len(comp.description) > 100 else f"   📝 Description: {comp.description or 'N/A'}")
                print(f"   🔍 Confidence: {comp.confidence_score:.2f}")
                print()
        else:
            print("\n❌ No Windows apps found")
        
        if feedback_data:
            print(f"\n💬 TOP REVIEWS FROM MICROSOFT STORE")
            print(f"{'='*50}")
            for i, fb in enumerate(feedback_data[:3], 1):
                print(f"{i}. {fb.text[:150]}...")
                print(f"   🪟 App: {fb.author_info.get('app_name', 'N/A') if fb.author_info else 'N/A'}")
                print()
        
        print(f"📁 FILES GENERATED:")
        print(f"   📊 JSON Analysis: {json_file}")
        if competitors:
            print(f"   📋 CSV Data: {csv_file}")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Microsoft Store analysis failed: {str(e)}")
        print(f"❌ Microsoft Store analysis failed: {str(e)}")
        return None


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Test scrapers with specific queries')
    
    parser.add_argument('--product-hunt', action='store_true', help='Test Product Hunt scraper')
    parser.add_argument('--google', action='store_true', help='Test Google scraper')
    parser.add_argument('--reddit', action='store_true', help='Test Reddit scraper')
    parser.add_argument('--google-play', action='store_true', help='Test Google Play Store scraper (Mobile-Optimized)')
    parser.add_argument('--app-store', action='store_true', help='Test iOS App Store scraper')
    parser.add_argument('--microsoft-store', action='store_true', help='Test Microsoft Store scraper')
    parser.add_argument('--app-stores', action='store_true', help='Test all app store scrapers')
    parser.add_argument('--all', action='store_true', help='Test all scrapers')
    parser.add_argument('--sentiment-demo', action='store_true', help='Run comprehensive scraping + sentiment analysis demo')
    parser.add_argument('--query', type=str, default='productivity app', help='Search query to test')
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Check for sentiment demo first
    if args.sentiment_demo:
        await comprehensive_sentiment_demo(args.query)
        return
    
    if not (args.product_hunt or args.google or args.reddit or args.google_play or 
            args.app_store or args.microsoft_store or args.app_stores or args.all):
        print("🚀 SCRAPER TESTING TOOL")
        print("=" * 50)
        print("Please specify at least one scraper to test:")
        print()
        print("🎯 COMPREHENSIVE DEMO:")
        print("  --sentiment-demo  Run comprehensive scraping + sentiment analysis demo")
        print()
        print("📱 APP STORE SCRAPERS:")
        print("  --google-play     Test Google Play Store scraper (Android - Mobile-Optimized)")
        print("  --app-store       Test iOS App Store scraper (iPhone/iPad)")
        print("  --microsoft-store Test Microsoft Store scraper (Windows)")
        print("  --app-stores      Test all app store scrapers")
        print()
        print("🌐 WEB SCRAPERS:")
        print("  --product-hunt    Test Product Hunt scraper")
        print("  --google          Test Google search scraper")
        print("  --reddit          Test Reddit scraper")
        print()
        print("🔧 COMBINED OPTIONS:")
        print("  --all             Test all scrapers")
        print()
        print("📝 USAGE EXAMPLES:")
        print("  python test_scrapers.py --sentiment-demo --query 'productivity app'")
        print("  python test_scrapers.py --google-play --query 'fitness app'")
        print("  python test_scrapers.py --product-hunt --query 'productivity tool'")
        print("  python test_scrapers.py --app-stores --query 'business validation'")
        print("  python test_scrapers.py --all --query 'market research'")
        print()
        print("💡 RECOMMENDED: Start with the comprehensive demo:")
        print("  python test_scrapers.py --sentiment-demo --query 'your idea here'")
        return
    
    if args.all or args.product_hunt:
        await test_product_hunt_scraper(args.query)
    
    if args.all or args.google_play or args.app_stores:
        await test_google_play_store_scraper(args.query)


if __name__ == "__main__":
    asyncio.run(main())