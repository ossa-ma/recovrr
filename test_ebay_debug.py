#!/usr/bin/env python3
"""Debug eBay scraper to see what's happening."""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from recovrr.scrapers.ebay_scraper import EbayScraper


async def debug_ebay_scraper():
    """Debug the eBay scraper to see what's happening."""
    print("🔧 Debugging eBay Scraper")
    print("=" * 40)
    
    scraper = EbayScraper()
    
    try:
        await scraper.start_session()
        print("✅ Session started successfully")
        
        # Test with a very common search term that should have results
        test_searches = [
            "bicycle",
            "bike",
            "specialized",
            "electric bike"
        ]
        
        for search_term in test_searches:
            print(f"\n🔍 Testing search: '{search_term}'")
            
            try:
                # Let's see the actual search URL being used
                search_url = f"https://www.ebay.com/sch/i.html?_nkw={search_term.replace(' ', '+')}"
                print(f"   URL: {search_url}")
                
                # Try the search
                results = await scraper.search(search_term)
                print(f"   Results: {len(results)} listings found")
                
                if results:
                    # Show first result details
                    first_result = results[0]
                    print("   Sample result:")
                    for key, value in first_result.items():
                        print(f"     {key}: {value}")
                    break  # Stop after first successful search
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        # If still no results, let's try a manual HTTP request to see what we get
        print("\n🌐 Testing raw HTTP request...")
        try:
            response = await scraper.session.get("https://www.ebay.com/sch/i.html?_nkw=bicycle")
            print(f"   Status Code: {response.status_code}")
            print(f"   Content Length: {len(response.text)} characters")
            
            # Check if we're getting blocked
            if "blocked" in response.text.lower() or "robot" in response.text.lower():
                print("   ⚠️  Possible bot detection/blocking")
            
            # Look for typical eBay elements
            if "ebay" in response.text.lower() and "search" in response.text.lower():
                print("   ✅ Got eBay search page")
            else:
                print("   ❌ Doesn't look like eBay search page")
                
            # Save response for manual inspection
            with open("ebay_response_debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("   📄 Response saved to 'ebay_response_debug.html'")
            
        except Exception as e:
            print(f"   ❌ HTTP Error: {e}")
            
    finally:
        await scraper.close_session()
        print("\n✅ Session closed")


if __name__ == "__main__":
    asyncio.run(debug_ebay_scraper())
