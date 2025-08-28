from recovrr.config.settings import settings
from recovrr.database.supabase import (
    search_profile_db,
    listing_db,
    analysis_result_db,
    dashboard_db,
)
from recovrr.models.search_profile import SearchProfile
from recovrr.scrapers.ebay_scraper import EbayScraper
from recovrr.scrapers.facebook_scraper import FacebookScraper
from recovrr.agents.matcher_agent import create_matcher_agent
from recovrr.notifications.notification_service import NotificationService
from recovrr.scheduler.monitoring_job import MonitoringJob

import asyncio


async def test_database():
    """Test database connection and operations."""
    print("🗄️ Testing Database Connection...")

    try:
        stats = await dashboard_db.get_dashboard_stats()
        print("Database connected successfully")
        print(f"Active profiles: {stats.get('active_profiles', 0)}")
        print(f"Total listings: {stats.get('total_listings', 0)}")
        print(f"Matches found: {stats.get('matches_found', 0)}")

        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Check your SUPABASE_URL and SUPABASE_KEY in .env")

        return False


async def test_ai_agent():
    """Test AI matching agent."""
    print("\n🤖 Testing AI Agent...")

    try:
        agent = create_matcher_agent()

        # Test listing
        test_listing = {
            "title": "Black Cannondale Synapse Road Bike - Great Condition",
            "description": "Selling my 56cm Cannondale Synapse. Black frame with some wear on the top tube.",
            "price": 500.0,
            "location": "London",
            "marketplace": "ebay",
            "url": "https://example.com/test",
        }

        # Test search profile
        test_profile = {
            "make": "Cannondale",
            "model": "Synapse",
            "color": "Black",
            "size": "56cm",
            "unique_features": "Scratch on top tube",
            "location": "London",
        }

        result = await agent.check_match(test_listing, test_profile)

        print("AI Agent working successfully")
        print(f"Match score: {result['match_score']}/10")
        print(f"Confidence: {result['confidence_level']}")
        print(f"Recommendation: {result['recommendation']}")
        print(f"Reasoning: {result['reasoning'][:100]}...")

        return True

    except Exception as e:
        print(f"AI Agent failed: {e}")
        print("Check your agents framework configuration for LLM API keys")

        return False


async def test_scrapers():
    """Test marketplace scrapers."""
    print("\n Testing Scrapers...")

    # Test eBay scraper
    try:
        print("  Testing eBay scraper...")
        ebay_scraper = EbayScraper()
        async with ebay_scraper:
            listings = await ebay_scraper.search("cannondale road bike", location="London")
            print(f"  ✅ eBay scraper: Found {len(listings)} listings")
            if listings:
                print(f"     Sample: {listings[0]['title'][:60]}...")
    except Exception as e:
        print(f"  eBay scraper failed: {e}")

    # Test Facebook scraper (may be more challenging due to anti-bot measures)
    try:
        print("  Testing Facebook scraper...")
        fb_scraper = FacebookScraper()
        async with fb_scraper:
            listings = await fb_scraper.search("cannondale road bike", location="London")
            print(f"  ✅ Facebook scraper: Found {len(listings)} listings")
            if listings:
                print(f"     Sample: {listings[0]['title'][:60]}...")
    except Exception as e:
        print(f"  Facebook scraper failed (this is common): {e}")
        print("     Facebook has strong anti-bot measures, this is expected")


async def test_notifications():
    """Test notification services."""
    print("\n  Testing Notifications...")

    notification_service = NotificationService()

    if not notification_service.is_configured():
        print("  No notification services configured")
        print("  Add SENDGRID_API_KEY and/or TWILIO_* keys to .env")
        return

    available_methods = notification_service.get_available_methods()
    print(f"  Available methods: {', '.join(available_methods)}")

    # Test with sample data
    test_profile = {
        "name": "Test Bike",
        "make": "Cannondale",
        "owner_email": "test@example.com",  # Change this to your email
        "owner_phone": "+1234567890",  # Change this to your phone
    }

    test_listing = {
        "title": "Test Listing - Black Cannondale",
        "price": 500,
        "url": "https://example.com/test",
        "marketplace": "test",
    }

    test_analysis = {
        "match_score": 8.5,
        "confidence_level": "high",
        "reasoning": "Strong match based on make, model, and color",
        "recommendation": "investigate",
    }

    try:
        results = await notification_service.send_match_alert(
            test_profile, test_listing, test_analysis
        )
        print(f"  Notification test results: {results}")
    except Exception as e:
        print(f"  Notification test failed: {e}")


async def create_test_profile():
    """Create a test search profile."""
    print("\n👤 Creating Test Search Profile...")

    try:
        # Create a test profile
        profile = SearchProfile(
            name="Test Stolen Bike",
            make="Cannondale",
            model="Synapse",
            color="Black",
            size="56cm",
            unique_features="Distinctive scratch on top tube, aftermarket brake levers",
            location="London",
            owner_email="test@example.com",  # Change this to your email
            owner_phone="+1234567890",  # Change this to your phone
        )

        saved_profile = await search_profile_db.create_search_profile(profile.to_db_dict())
        print(f"Created test profile: {saved_profile.name} (ID: {saved_profile.id})")
        return saved_profile.id

    except Exception as e:
        print(f"Failed to create test profile: {e}")
        return None


async def run_monitoring_cycle():
    """Run a complete monitoring cycle."""
    print("\n Running Complete Monitoring Cycle...")

    try:
        job = MonitoringJob()
        result = await job.run_monitoring_cycle()

        print("Monitoring cycle completed:")
        print(f"   Duration: {result['duration_seconds']:.1f} seconds")
        print(f"   Search profiles: {result['search_profiles']}")
        print(f"   New listings: {result['new_listings']}")
        print(f"   Matches found: {result['matches_found']}")
        print(f"   Notifications sent: {result['notifications_sent']}")

        return True

    except Exception as e:
        print(f"Monitoring cycle failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Recovrr Manual Testing")
    print("=" * 50)

    # Test each component
    db_ok = await test_database()
    if not db_ok:
        print("\nDatabase test failed - stopping here")
        return

    ai_ok = await test_ai_agent()

    await test_scrapers()
    await test_notifications()

    # Create test profile if database and AI are working
    if db_ok and ai_ok:
        profile_id = await create_test_profile()

        if profile_id:
            await run_monitoring_cycle()

    print("\n" + "=" * 50)
    print("Testing Complete!")
    print("\nNext Steps:")
    print("   1. Fix any failed tests by checking your .env configuration")
    print("   2. Create your real search profile with your bike details")
    print("   3. Start continuous monitoring with the scheduler")
    print("   4. Monitor your Supabase dashboard for results")


if __name__ == "__main__":
    asyncio.run(main())
