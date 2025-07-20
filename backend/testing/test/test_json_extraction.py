"""
Test JSON extraction from Product Hunt HTML.
"""
import re
import json
from unittest.mock import MagicMock
import sys

# Mock the config
sys.modules['app.config'] = MagicMock()

def test_json_extraction():
    """Test extracting JSON data from the saved HTML."""
    print("🔍 Testing JSON extraction from Product Hunt HTML...")
    
    try:
        # Read the saved HTML file
        with open('product_hunt_debug.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        print(f"📄 HTML length: {len(html)} characters")
        
        # Look for the specific JSON data we saw in the debug output
        # The data contains: "productSearch":{"__typename":"ProductSearchConnection","edges":[...
        
        # Pattern to find the productSearch data
        patterns = [
            r'"productSearch":\s*({[^}]*"edges":\s*\[[^\]]*\][^}]*})',
            r'"data":\s*({[^}]*"productSearch"[^}]*})',
            r'{"__typename":"ProductSearchConnection","edges":\[([^\]]*)\]',
        ]
        
        for i, pattern in enumerate(patterns):
            print(f"\n🔍 Trying pattern {i+1}: {pattern[:50]}...")
            matches = re.findall(pattern, html, re.DOTALL)
            print(f"Found {len(matches)} matches")
            
            for j, match in enumerate(matches[:2]):  # Show first 2 matches
                print(f"\nMatch {j+1} preview (first 200 chars):")
                print(match[:200] + "..." if len(match) > 200 else match)
                
                # Try to parse as JSON
                try:
                    if pattern.startswith('"data"'):
                        # This might be a larger object
                        data = json.loads(match)
                        print(f"✅ Successfully parsed JSON with keys: {list(data.keys())}")
                        
                        if 'productSearch' in data:
                            product_search = data['productSearch']
                            if 'edges' in product_search:
                                print(f"📊 Found {len(product_search['edges'])} products")
                                
                                # Show first product
                                if product_search['edges']:
                                    first_product = product_search['edges'][0]['node']
                                    print(f"First product: {first_product.get('name', 'Unknown')}")
                                    print(f"Description: {first_product.get('tagline', 'No description')}")
                    
                    elif pattern.startswith('"productSearch"'):
                        # Direct productSearch object
                        cleaned_match = match.replace('undefined', 'null')
                        data = json.loads(cleaned_match)
                        print(f"✅ Successfully parsed productSearch with keys: {list(data.keys())}")
                        
                        if 'edges' in data:
                            print(f"📊 Found {len(data['edges'])} products")
                            
                            # Show first product
                            if data['edges']:
                                first_product = data['edges'][0]['node']
                                print(f"First product: {first_product.get('name', 'Unknown')}")
                                print(f"Description: {first_product.get('tagline', 'No description')}")
                    
                    else:
                        # Edges array content
                        print("📊 Found edges array content")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {str(e)}")
                except Exception as e:
                    print(f"❌ Error processing match: {str(e)}")
        
        # Also try to find the exact string we saw in the debug output
        print("\n🔍 Looking for specific product data...")
        
        # Look for the CRM products we know are there
        crm_products = ['CRM Chat', 'Doplac CRM', 'folk', 'ChartMogul CRM']
        
        for product_name in crm_products:
            if product_name in html:
                print(f"✅ Found '{product_name}' in HTML")
                
                # Find the context around this product
                start_pos = html.find(product_name)
                context_start = max(0, start_pos - 200)
                context_end = min(len(html), start_pos + 500)
                context = html[context_start:context_end]
                
                print(f"Context around '{product_name}':")
                print(context)
                print("-" * 50)
            else:
                print(f"❌ '{product_name}' not found in HTML")
        
    except FileNotFoundError:
        print("❌ product_hunt_debug.html not found. Run debug_product_hunt.py first.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_json_extraction()