#!/usr/bin/env python3
"""Test script for searching Specialized Vado SL 4.0 electric bike on eBay."""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from recovrr.scrapers.ebay_scraper import EbayScraper
from recovrr.models.search_profile import SearchProfile


async def test_vado_search():
    """Test searching for Specialized Vado SL 4.0 electric bike."""
    print("🔍 Testing eBay Search for Specialized Vado SL 4.0")
    print("=" * 50)
    
    # Create a search profile for your bike
    search_profile = SearchProfile(
        name="Specialized Vado SL 4.0 Test",
        make="Specialized",
        model="Vado SL 4.0",
        color="Lime",
        description="Electric bike, Specialized Vado SL 4.0",
        search_terms=["specialized", "vado", "electric bike", "e-bike"],
        owner_email="test@example.com",
        location="Test Location"
    )
    
    print(f"Search Profile: {search_profile.name}")
    print(f"Make: {search_profile.make}")
    print(f"Model: {search_profile.model}")
    print(f"Color: {search_profile.color}")
    print(f"Search Terms: {search_profile.search_terms}")
    print()
    
    # Test different search strategies
    search_strategies = [
        {
            "name": "Full Model Search",
            "terms": "Specialized Vado SL 4.0",
            "description": "Complete model name"
        },
        {
            "name": "Broader Vado Search", 
            "terms": "Specialized Vado electric bike",
            "description": "Broader search without specific model"
        },
        {
            "name": "E-bike Search",
            "terms": "Specialized electric bike",
            "description": "General electric bike search"
        },
        {
            "name": "Just Brand + Model",
            "terms": "Specialized Vado",
            "description": "Brand and model line only"
        }
    ]
    
    scraper = EbayScraper()
    
    try:
        await scraper.start_session()
        
        for strategy in search_strategies:
            print(f"🔍 Testing: {strategy['name']}")
            print(f"   Search Terms: '{strategy['terms']}'")
            print(f"   Strategy: {strategy['description']}")
            
            try:
                results = await scraper.search(strategy['terms'])
                print(f"   ✅ Found {len(results)} listings")
                
                if results:
                    print("   📋 Sample listings:")
                    for i, listing in enumerate(results[:3]):  # Show first 3
                        print(f"      {i+1}. {listing.get('title', 'No title')[:80]}...")
                        print(f"         Price: ${listing.get('price', 'Unknown')}")
                        print(f"         Location: {listing.get('location', 'Unknown')}")
                        print()
                else:
                    print("   ❌ No listings found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print("-" * 50)
        
        # Test the search profile method
        print("🔍 Testing Search Profile Method")
        try:
            profile_results = await scraper.scrape_search_profile(search_profile.to_search_dict())
            print(f"✅ Search profile method found {len(profile_results)} listings")
            
            if profile_results:
                print("📋 Profile search results:")
                for i, listing in enumerate(profile_results[:2]):
                    print(f"   {i+1}. {listing.get('title', 'No title')[:80]}...")
                    print(f"      Price: ${listing.get('price', 'Unknown')}")
                    print(f"      URL: {listing.get('url', 'No URL')}")
                    print()
        
        except Exception as e:
            print(f"❌ Profile search error: {e}")
            
    finally:
        await scraper.close_session()
    
    print("=" * 50)
    print("🎯 Recommendations:")
    print("1. If few/no results: Try broader terms like 'Specialized electric bike'")
    print("2. Monitor multiple search terms for better coverage")
    print("3. Consider color-specific searches if needed: 'Specialized Vado lime'")
    print("4. eBay search is case-insensitive and partial-match friendly")


if __name__ == "__main__":
    asyncio.run(test_vado_search())
