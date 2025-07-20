"""
Debug script to examine individual Product Hunt product pages for detailed information.
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
import sys
from unittest.mock import MagicMock

# Mock the config
sys.modules['app.config'] = MagicMock()


async def debug_product_page():
    """Debug a specific Product Hunt product page."""
    print("🔍 Debugging Product Hunt product page...")
    
    # Use one of the CRM products we found
    product_url = "https://www.producthunt.com/posts/folk-2"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            print(f"📡 Fetching: {product_url}")
            
            async with session.get(product_url) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    html = await response.text()
                    print(f"📄 HTML length: {len(html)} characters")
                    
                    # Save raw HTML for inspection
                    with open('product_hunt_product_debug.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print("💾 Raw HTML saved to: product_hunt_product_debug.html")
                    
                    # Parse and analyze structure
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    print("\n🔍 Looking for structured data...")
                    
                    # Look for JSON-LD structured data
                    json_ld_scripts = soup.find_all('script', type='application/ld+json')
                    for i, script in enumerate(json_ld_scripts):
                        try:
                            data = json.loads(script.string)
                            print(f"📋 JSON-LD {i+1}:")
                            print(json.dumps(data, indent=2)[:500] + "...")
                            
                            # Save full JSON for inspection
                            with open(f'structured_data_{i+1}.json', 'w') as f:
                                json.dump(data, f, indent=2)
                                
                        except json.JSONDecodeError:
                            print(f"❌ Failed to parse JSON-LD {i+1}")
                    
                    # Look for Apollo SSR data (like in search results)
                    print("\n🔍 Looking for Apollo SSR data...")
                    json_pattern = r'window\[Symbol\.for\("ApolloSSRDataTransport"\)\].*?\.push\(({.*?})\)'
                    matches = re.findall(json_pattern, html, re.DOTALL)
                    
                    for i, match in enumerate(matches):
                        try:
                            data = json.loads(match)
                            print(f"📋 Apollo SSR Data {i+1} keys: {list(data.keys())}")
                            
                            # Look for product-specific data
                            if 'rehydrate' in data:
                                rehydrate = data['rehydrate']
                                for key, value in rehydrate.items():
                                    if isinstance(value, dict) and 'data' in value:
                                        data_obj = value['data']
                                        if isinstance(data_obj, dict):
                                            print(f"  Data object keys: {list(data_obj.keys())}")
                                            
                                            # Look for reviews, launch date, founder info
                                            if 'reviews' in str(data_obj).lower():
                                                print("  🎯 Found reviews data!")
                                            if 'launch' in str(data_obj).lower():
                                                print("  🎯 Found launch data!")
                                            if 'maker' in str(data_obj).lower() or 'founder' in str(data_obj).lower():
                                                print("  🎯 Found maker/founder data!")
                                                
                        except json.JSONDecodeError:
                            continue
                    
                    # Look for specific HTML elements
                    print("\n🔍 Looking for HTML elements...")
                    
                    # Reviews
                    review_elements = soup.find_all(text=re.compile(r'review', re.I))
                    print(f"📝 Found {len(review_elements)} review-related text elements")
                    
                    # Launch date
                    date_elements = soup.find_all(text=re.compile(r'\d{4}|\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2}'))
                    print(f"📅 Found {len(date_elements)} date-like text elements")
                    
                    # Maker/Founder
                    maker_elements = soup.find_all(text=re.compile(r'maker|founder|ceo|creator', re.I))
                    print(f"👤 Found {len(maker_elements)} maker/founder-related text elements")
                    
                    # Look for common class patterns
                    print("\n🏷️ Common class patterns:")
                    all_classes = set()
                    for element in soup.find_all(class_=True):
                        if isinstance(element.get('class'), list):
                            all_classes.update(element.get('class'))
                    
                    # Filter for potentially relevant classes
                    relevant_classes = [cls for cls in all_classes if any(keyword in cls.lower() 
                                      for keyword in ['review', 'comment', 'maker', 'founder', 'date', 'launch', 'rating'])]
                    
                    for cls in sorted(relevant_classes)[:20]:  # Show first 20
                        print(f"    .{cls}")
                
                else:
                    print(f"❌ Failed to fetch page: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🐛 Product Hunt Product Page Debug Tool")
    print("=" * 50)
    
    asyncio.run(debug_product_page())
    
    print("\n✨ Debug completed!")