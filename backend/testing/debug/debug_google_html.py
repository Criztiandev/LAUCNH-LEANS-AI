#!/usr/bin/env python3
"""
Debug script to see what HTML Google is returning.
"""
import asyncio
import aiohttp
import random
from urllib.parse import quote_plus

async def debug_google_search():
    """Debug Google search to see what HTML we get."""
    
    query = "CRM software"
    encoded_query = quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}&num=10"
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    print(f"Searching for: {query}")
    print(f"URL: {url}")
    print(f"User-Agent: {headers['User-Agent']}")
    print("\n" + "="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"Status Code: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Save the HTML to a file for inspection
                    with open('google_debug_response.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    print(f"HTML length: {len(html_content)} characters")
                    print(f"HTML saved to: google_debug_response.html")
                    
                    # Show first 1000 characters
                    print("\nFirst 1000 characters of HTML:")
                    print("-" * 40)
                    print(html_content[:1000])
                    print("-" * 40)
                    
                    # Check for common Google elements
                    if "div class=\"g\"" in html_content:
                        print("\n✓ Found search result divs (div.g)")
                    else:
                        print("\n✗ No search result divs found")
                    
                    if "h3" in html_content:
                        print("✓ Found h3 elements")
                    else:
                        print("✗ No h3 elements found")
                    
                    if "captcha" in html_content.lower():
                        print("⚠️  CAPTCHA detected in response")
                    
                    if "blocked" in html_content.lower():
                        print("⚠️  Blocking message detected")
                        
                else:
                    print(f"Request failed with status: {response.status}")
                    error_text = await response.text()
                    print(f"Error response: {error_text[:500]}")
                    
    except Exception as e:
        print(f"Request failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_google_search())