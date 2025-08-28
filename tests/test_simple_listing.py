#!/usr/bin/env python3
"""Test script for simple Listing model approach."""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from recovrr.scrapers.ebay_scraper import EbayScraper
from recovrr.models.listing import Listing


async def test_simple_listing_model():
    """Test that eBay scraper returns clean Listing objects."""
    print("🧪 Testing Simple Listing Model")
    print("=" * 50)
    
    scraper = EbayScraper()
    
    try:
        await scraper.start_session()
        
        # Test search
        search_term = "Specialized Vado SL 4.0"
        print(f"🔍 Searching for: '{search_term}'")
        
        results = await scraper.search(search_term)
        print(f"✅ Found {len(results)} Listing objects")
        
        if not results:
            print("❌ No results found")
            return
        
        # Test first result
        first_listing = results[0]
        print(f"\n📋 First Listing:")
        print(f"   Type: {type(first_listing)}")
        print(f"   Is Listing: {isinstance(first_listing, Listing)}")
        
        if isinstance(first_listing, Listing):
            # Test the simple, clean structure
            print(f"\n🔍 Listing Details:")
            print(f"   ID: {first_listing.external_id}")
            print(f"   Source: {first_listing.source}")
            print(f"   Title: {first_listing.title[:60]}...")
            print(f"   Price: {first_listing.format_price()}")
            print(f"   Location: {first_listing.location}")
            print(f"   Description: {first_listing.description[:50]}...")
            print(f"   Images: {len(first_listing.images)} image(s)")
            print(f"   Primary image: {first_listing.get_primary_image()[:60] + '...' if first_listing.get_primary_image() else 'None'}")
            
            # Test conversion to dict
            listing_dict = first_listing.to_dict()
            print(f"\n🔄 Dictionary Conversion:")
            print(f"   Dict keys: {list(listing_dict.keys())}")
            print(f"   Clean structure: {bool(listing_dict['external_id'] and listing_dict['title'])}")
            
            # Test string representation
            print(f"\n📝 String representation:")
            print(f"   {str(first_listing)}")
            
        # Test multiple listings consistency
        print(f"\n🔄 Testing {min(5, len(results))} Listings:")
        
        all_valid = True
        for i, listing in enumerate(results[:5]):
            if not isinstance(listing, Listing):
                print(f"   ❌ Result {i+1}: Not a Listing object")
                all_valid = False
            elif not listing.external_id or not listing.title:
                print(f"   ❌ Result {i+1}: Missing required fields")
                all_valid = False
            else:
                print(f"   ✅ Result {i+1}: {listing.source} - {listing.title[:40]}...")
                
        print(f"\n📊 Summary:")
        print(f"   All results valid: {all_valid}")
        print(f"   All from eBay: {all(r.source == 'ebay' for r in results if isinstance(r, Listing))}")
        print(f"   With prices: {sum(1 for r in results if isinstance(r, Listing) and r.price)}/{len(results)}")
        print(f"   With images: {sum(1 for r in results if isinstance(r, Listing) and r.images)}/{len(results)}")
        
    finally:
        await scraper.close_session()
    
    print("\n" + "=" * 50)
    print("✅ Simple Listing Model Test Complete!")
    print("\n🎯 Benefits of This Approach:")
    print("   • Simple, readable Pydantic model")
    print("   • Type safety without over-engineering")
    print("   • Easy to extend for new marketplaces")
    print("   • Clean conversion to dict/JSON")
    print("   • Useful helper methods")
    print("   • Maintainable for new developers")


if __name__ == "__main__":
    asyncio.run(test_simple_listing_model())
