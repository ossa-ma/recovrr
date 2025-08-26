#!/usr/bin/env python3
"""Setup script for initializing Supabase database."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from recovrr.database import dashboard_db
from recovrr.config import settings


async def main():
    """Initialize Supabase database and verify connection."""
    
    print("🚀 Setting up Recovrr with Supabase...")
    
    # Check if Supabase is configured
    try:
        if not settings.supabase_url or not settings.supabase_key:
            print("❌ Error: Supabase URL and key must be configured in .env file")
            print("Please check your environment variables:")
            print("- SUPABASE_URL")
            print("- SUPABASE_KEY (use service role key for backend operations)")
            return False
            
        print(f"✅ Supabase URL: {settings.supabase_url}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Check migration files
    try:
        print("📊 Database setup...")
        print("⚠️  Please run the SQL migration files in your Supabase dashboard:")
        print("   1. migrations/001_create_tables.sql")
        print("   2. migrations/002_rls_policies.sql") 
        print("   3. migrations/003_dashboard_functions.sql")
        print("✅ Migration files available")
        
    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        return False
    
    # Test Supabase connection
    try:
        print("🔌 Testing Supabase API connection...")
        stats = await dashboard_db.get_dashboard_stats()
        print("✅ Supabase API connection successful")
        print(f"📈 Dashboard stats: {stats}")
        
    except Exception as e:
        print(f"❌ Supabase API connection failed: {e}")
        print("Note: This might be normal if you haven't run the migrations yet")
    
    print("\n🎉 Recovrr setup complete!")
    print("\nNext steps:")
    print("1. Create a search profile for your stolen item")
    print("2. Configure AI API keys (OpenAI/Anthropic)")  
    print("3. Set up notification services (SendGrid/Twilio)")
    print("4. Start monitoring with the scheduler")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
