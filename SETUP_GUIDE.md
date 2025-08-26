# Recovrr Setup Guide 🚀

Complete step-by-step guide to get Recovrr running for bike theft monitoring.

## 📋 Prerequisites

- Python 3.13+
- `uv` package manager
- A Supabase account

## 🔧 1. Environment Setup

### Clone and Install Dependencies
```bash
cd /Users/ossama/Documents/Projects/recovrr
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 🗄️ 2. Supabase Database Setup

### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Choose organization and name your project `recovrr`
4. Set a strong database password (save this!)
5. Choose region closest to you
6. Click "Create new project"

### Step 2: Get Your Credentials
Once your project is created:

1. **Get Project URL**: 
   - In dashboard, go to Settings → API
   - Copy "Project URL" (e.g., `https://abc123.supabase.co`)

2. **Get Service Role Key**:
   - Still in Settings → API
   - Copy "service_role" key (NOT the anon key)
   - This key bypasses RLS for backend operations

### Step 3: Run Database Migrations
In your Supabase dashboard:

1. Go to SQL Editor (left sidebar)
2. Click "New Query"
3. Copy and run each migration file in order:

**Migration 1** - Copy contents of `migrations/001_create_tables.sql`:
```sql
-- Copy the entire contents of migrations/001_create_tables.sql and run it
```

**Migration 2** - Copy contents of `migrations/002_rls_policies.sql`:
```sql
-- Copy the entire contents of migrations/002_rls_policies.sql and run it
```

**Migration 3** - Copy contents of `migrations/003_dashboard_functions.sql`:
```sql
-- Copy the entire contents of migrations/003_dashboard_functions.sql and run it
```

## 🔑 3. Environment Variables Setup

Create your `.env` file:
```bash
cp env.example .env
```

### Configure Supabase
Edit `.env` and add your Supabase credentials:
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

## 🤖 4. AI API Keys Setup

### OpenAI (Recommended)
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account or sign in
3. Go to API Keys section
4. Click "Create new secret key"
5. Copy the key and add to `.env`:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
```

### Anthropic (Alternative)
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create account or sign in
3. Go to API Keys
4. Generate new key
5. Add to `.env`:
```bash
ANTHROPIC_API_KEY=your-anthropic-key-here
```

## 📧 5. Notification Services Setup

### Email Notifications (SendGrid)
1. Go to [sendgrid.com](https://sendgrid.com)
2. Create free account (100 emails/day free)
3. Go to Settings → API Keys
4. Create new API key with "Full Access"
5. Add to `.env`:
```bash
SENDGRID_API_KEY=SG.your-sendgrid-key-here
```

### SMS Notifications (Twilio)
1. Go to [twilio.com](https://twilio.com)
2. Create free account ($15 credit)
3. Go to Console Dashboard
4. Find your Account SID and Auth Token
5. Buy a phone number (Phone Numbers → Manage → Buy a number)
6. Add to `.env`:
```bash
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

## ✅ 6. Test Your Setup

### Test Database Connection
```bash
python -c "
import asyncio
from recovrr.database.supabase_db import dashboard_db

async def test():
    stats = await dashboard_db.get_dashboard_stats()
    print('✅ Database connected:', stats)

asyncio.run(test())
"
```

### Test AI Agent
```bash
python -c "
import asyncio
from recovrr.agents.matcher_agent import MatcherAgent

async def test():
    agent = MatcherAgent()
    result = await agent.check_match(
        {'title': 'Black Cannondale Road Bike', 'price': 500, 'location': 'London'},
        {'make': 'Cannondale', 'color': 'Black', 'location': 'London'}
    )
    print('✅ AI Agent working:', result['match_score'])

asyncio.run(test())
"
```

## 🚴 7. Create Your First Search Profile

Run this to create a search profile for your stolen bike:

```bash
python -c "
import asyncio
from recovrr.database.supabase_db import search_profile_db
from recovrr.models.search_profile import SearchProfile

async def create_profile():
    profile = SearchProfile(
        name='My Stolen Cannondale',
        make='Cannondale',
        model='Synapse',  # Replace with your bike model
        color='Black',    # Replace with your bike color
        size='56cm',      # Replace with your frame size
        unique_features='Distinctive scratch on top tube, aftermarket brake levers',  # Describe unique features
        location='London', # Where it was stolen
        owner_email='your-email@example.com',  # Your email for alerts
        owner_phone='+1234567890'  # Your phone for SMS alerts
    )
    
    saved = await search_profile_db.create_search_profile(profile.to_db_dict())
    print(f'✅ Created search profile: {saved.name} (ID: {saved.id})')

asyncio.run(create_profile())
"
```

## 🕵️ 8. Manual Testing

### Test eBay Scraping
```bash
python -c "
import asyncio
from recovrr.scrapers.ebay_scraper import EbayScraper

async def test_ebay():
    scraper = EbayScraper()
    async with scraper:
        listings = await scraper.search('cannondale road bike')
        print(f'✅ Found {len(listings)} eBay listings')
        if listings:
            print(f'Sample: {listings[0]['title'][:50]}...')

asyncio.run(test_ebay())
"
```

### Run One Complete Monitoring Cycle
```bash
python -c "
import asyncio
from recovrr.scheduler.monitoring_job import MonitoringJob

async def test_monitoring():
    job = MonitoringJob()
    result = await job.run_monitoring_cycle()
    print('✅ Monitoring cycle complete:')
    print(f'  - Search profiles: {result['search_profiles']}')
    print(f'  - New listings: {result['new_listings']}')
    print(f'  - Matches found: {result['matches_found']}')
    print(f'  - Notifications sent: {result['notifications_sent']}')

asyncio.run(test_monitoring())
"
```

## 🚀 9. Start Continuous Monitoring

### Run the Scheduler
```bash
python -c "
import asyncio
from recovrr.scheduler.scheduler_service import main

# This will run continuous monitoring every 15 minutes
# Press Ctrl+C to stop
asyncio.run(main())
"
```

## 📊 10. Monitor Your Data

### Check Your Supabase Dashboard
1. Go to your Supabase project
2. Click "Table editor"
3. View your data in tables:
   - `search_profiles` - Your bike profiles
   - `listings` - Scraped marketplace listings
   - `analysis_results` - AI match results

### Check for Notifications
- **Email**: Check your inbox for match alerts
- **SMS**: Check your phone for high-priority matches

## ⚙️ 11. Configuration Options

Edit `.env` to customize:

```bash
# Monitoring frequency (minutes)
SCRAPE_INTERVAL_MINUTES=15

# AI matching threshold (0-10)
MATCH_THRESHOLD=7.0

# Concurrent scrapers
MAX_CONCURRENT_SCRAPERS=3

# Request delays (seconds)
REQUEST_DELAY_SECONDS=1.0
```

## 🔧 12. Troubleshooting

### Common Issues

**"No module named 'recovrr'"**
```bash
# Run from project root with PYTHONPATH
PYTHONPATH=/Users/ossama/Documents/Projects/recovrr python -c "..."
```

**Supabase connection failed**
- Check your SUPABASE_URL and SUPABASE_KEY
- Ensure you're using the service_role key, not anon key
- Verify your project is not paused

**AI agent errors**
- Check your OpenAI/Anthropic API key
- Ensure you have credits/quota remaining

**No notifications received**
- Verify SendGrid/Twilio credentials
- Check spam folder for emails
- Test with a manual notification first

### Support
- Check Supabase logs in dashboard
- Review Python error messages
- Ensure all migrations ran successfully

You're now ready to monitor for your stolen bike! 🚴‍♂️🔍
