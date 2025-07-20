"""
Debug script to see what HTML structure Product Hunt actually returns.
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sys
from urllib.parse import quote_plus

# Mock the config
from unittest.mock import MagicMock
sys.modules['app.config'] = MagicMock()


async def debug_product_hunt_html():
    """Debug Product Hunt HTML structure."""
    print("🔍 Debugging Product Hunt HTML structure...")
    
    base_url = "https://www.producthunt.com"
    search_url = f"{base_url}/search"
    keyword = "CRM"
    
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
            # Try the search URL
            search_params = f"?q={quote_plus(keyword)}"
            url = f"{search_url}{search_params}"
            
            print(f"📡 Fetching: {url}")
            
            async with session.get(url) as response:
                print(f"📊 Response status: {response.status}")
                print(f"📋 Response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    html = await response.text()
                    print(f"📄 HTML length: {len(html)} characters")
                    
                    # Save raw HTML for inspection
                    with open('product_hunt_debug.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print("💾 Raw HTML saved to: product_hunt_debug.html")
                    
                    # Parse and analyze structure
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    print("\n🔍 Analyzing HTML structure...")
                    
                    # Look for various potential product containers
                    selectors_to_try = [
                        ('div.styles_item__Dk_nz', 'Product Hunt specific selector'),
                        ('div[class*="item"]', 'Generic item divs'),
                        ('div[class*="product"]', 'Product-related divs'),
                        ('div[class*="card"]', 'Card-style divs'),
                        ('article', 'Article elements'),
                        ('a[href*="/posts/"]', 'Post links'),
                        ('div[data-test*="product"]', 'Data-test product elements'),
                        ('div[role="listitem"]', 'List item roles'),
                    ]
                    
                    for selector, description in selectors_to_try:
                        elements = soup.select(selector)
                        print(f"  {description}: {len(elements)} elements found")
                        
                        if elements and len(elements) > 0:
                            print(f"    First element preview: {str(elements[0])[:200]}...")
                    
                    # Look for common class patterns
                    print("\n🏷️ Common class patterns:")
                    all_classes = set()
                    for element in soup.find_all(class_=True):
                        if isinstance(element.get('class'), list):
                            all_classes.update(element.get('class'))
                    
                    # Filter for potentially relevant classes
                    relevant_classes = [cls for cls in all_classes if any(keyword in cls.lower() 
                                      for keyword in ['item', 'product', 'card', 'post', 'result', 'list'])]
                    
                    for cls in sorted(relevant_classes)[:20]:  # Show first 20
                        print(f"    .{cls}")
                    
                    # Look for text content that might be products
                    print("\n📝 Text content analysis:")
                    text_elements = soup.find_all(text=True)
                    crm_related = [text.strip() for text in text_elements 
                                 if text.strip() and 'crm' in text.strip().lower()]
                    
                    print(f"  Found {len(crm_related)} CRM-related text elements:")
                    for text in crm_related[:10]:  # Show first 10
                        print(f"    '{text}'")
                
                else:
                    print(f"❌ Failed to fetch page: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🐛 Product Hunt HTML Debug Tool")
    print("=" * 50)
    
    asyncio.run(debug_product_hunt_html())
    
    print("\n✨ Debug completed!")