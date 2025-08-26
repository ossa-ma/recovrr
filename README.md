# Recovrr 🔍

**Scalable Marketplace Monitoring System for Stolen Item Recovery**

Recovrr is an intelligent monitoring system that automatically tracks multiple online marketplaces for stolen items using AI-powered analysis. It continuously scrapes listings, analyzes them against stolen item profiles, and sends intelligent notifications when potential matches are found.

## 🎯 Core Features

- **Multi-Marketplace Monitoring**: Supports eBay, Facebook Marketplace, and more
- **AI-Powered Matching**: Uses advanced LLMs to intelligently analyze listings
- **Smart Notifications**: Email and SMS alerts with confidence scoring
- **Automated Scheduling**: Continuous monitoring with configurable intervals
- **Scalable Architecture**: Modular design supporting multiple users and items

## 🏗️ Architecture

The system is built with modularity and scalability in mind:

```
recovrr/
├── agents/          # AI agents for item matching
├── scrapers/        # Marketplace scrapers (eBay, Facebook, etc.)
├── database/        # Data models and database management
├── notifications/   # Email and SMS notification services
├── scheduler/       # Job scheduling and orchestration
├── config/          # Configuration and settings management
└── utils/          # Utility functions and helpers
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- `uv` package manager
- Supabase project (database and API)
- API keys for AI services (OpenAI/Anthropic)
- Optional: SendGrid (email), Twilio (SMS) for notifications

### Installation

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd recovrr
   
   # Create virtual environment with Python 3.13
   uv venv --python 3.13
   source .venv/bin/activate
   
   # Install dependencies
   uv pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and settings
   ```

3. **Set up Supabase:**
   
   a. Create a new project at [supabase.com](https://supabase.com)
   
   b. Get your project details:
   - Project URL: `https://your-project-id.supabase.co`
   - Anon Key: From Settings > API
   - Database Password: From Settings > Database
   
   c. Update your `.env` file:
   ```bash
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_DB_PASSWORD=your_database_password
   ```
   
   d. Initialize database tables:
   ```python
   from recovrr.database import init_db
   init_db()  # Creates tables in your Supabase database
   ```

4. **Install browser for Facebook scraping:**
   ```bash
   python -m playwright install chromium
   ```

### Basic Usage

#### 1. Create a Search Profile

```python
from recovrr.database import get_session, SearchProfile

# Create search profile for stolen bike
profile = SearchProfile(
    name="My Stolen Cannondale",
    make="Cannondale",
    model="Synapse",
    color="Black with green trim",
    size="56cm",
    unique_features="Distinctive scratch on top tube, aftermarket handlebar tape",
    location="London",
    owner_email="victim@example.com",
    owner_phone="+1234567890"
)

with get_session() as db:
    db.add(profile)
    db.commit()
```

#### 2. Run Monitoring Manually

```python
import asyncio
from recovrr.scheduler import MonitoringJob

async def run_once():
    job = MonitoringJob()
    result = await job.run_monitoring_cycle()
    print(f"Found {result['new_listings']} new listings")
    print(f"Detected {result['matches_found']} potential matches")

asyncio.run(run_once())
```

#### 3. Start Continuous Monitoring

```python
import asyncio
from recovrr.scheduler import SchedulerService

async def start_monitoring():
    scheduler = SchedulerService()
    await scheduler.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await scheduler.stop()

asyncio.run(start_monitoring())
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Supabase Database
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_DB_PASSWORD=your_database_password

# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Notifications
SENDGRID_API_KEY=your_sendgrid_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone

# Scraping
SCRAPE_INTERVAL_MINUTES=15
MAX_CONCURRENT_SCRAPERS=3
REQUEST_DELAY_SECONDS=1.0

# Analysis
MATCH_THRESHOLD=7.0

# Application
DEBUG=false
LOG_LEVEL=INFO
```

### Search Profile Schema

Search profiles define what to look for:

```python
{
    "make": "Cannondale",           # Item manufacturer
    "model": "Synapse",             # Specific model
    "color": "Black",               # Primary color
    "size": "56cm",                 # Size specification
    "description": "Road bike...",   # General description
    "unique_features": "Scratch...", # Distinctive features
    "location": "London",           # Where it was stolen
    "search_terms": ["road bike"],  # Additional keywords
    "owner_email": "user@example.com",
    "owner_phone": "+1234567890"
}
```

## 🤖 AI Analysis

The system uses AI agents to intelligently analyze listings:

### Match Scoring (0-10 scale)
- **9-10**: Very high confidence match
- **7-8**: High confidence (triggers notifications)
- **5-6**: Moderate confidence
- **3-4**: Low confidence
- **1-2**: Very low confidence
- **0**: No match

### Analysis Factors
- Make and model matching
- Physical characteristics (color, size)
- Unique features and modifications
- Geographic proximity
- Price analysis (unusually low prices)
- Seller behavior patterns

## 📱 Notifications

### Email Notifications
- Rich HTML formatting with match details
- Includes reasoning and confidence scores
- Direct links to listings
- Clear next-step instructions

### SMS Notifications
- Sent for high-priority matches (score ≥ 8)
- Concise format with essential details
- Immediate alerts for urgent cases

### Notification Content
- Match confidence and score
- Item comparison details
- Listing information and link
- AI reasoning and key indicators
- Safety instructions (contact police, not seller)

## 🕷️ Supported Marketplaces

### Currently Supported
- **eBay**: Full support with search and detailed listing extraction
- **Facebook Marketplace**: Browser automation for JavaScript-heavy site

### Adding New Marketplaces
Extend the `BaseScraper` class:

```python
from recovrr.scrapers import BaseScraper

class NewMarketplaceScraper(BaseScraper):
    def __init__(self):
        super().__init__("new_marketplace")
    
    async def search(self, search_terms, location=None):
        # Implement marketplace-specific search logic
        pass
    
    def _parse_listing(self, listing_element):
        # Parse individual listings
        pass

# Register the scraper
from recovrr.scrapers import ScraperFactory
ScraperFactory.register_scraper("new_marketplace", NewMarketplaceScraper)
```

## 🗄️ Supabase Integration

### Why Supabase?

Recovrr uses **Supabase** as its database platform, which provides:

- **Managed PostgreSQL**: No database administration required
- **Real-time Subscriptions**: Get notified instantly when matches are found
- **Built-in APIs**: REST and GraphQL APIs automatically generated
- **Dashboard**: Visual interface to view your data
- **Row Level Security**: Built-in data protection
- **Automatic Backups**: Your data is safely backed up

### Supabase Features Used

1. **PostgreSQL Database**: Stores all listings, profiles, and analysis results
2. **Real-time API**: Optional instant notifications via websockets
3. **REST API**: Direct database queries when needed
4. **Dashboard**: View statistics and manage data visually

### Database Schema

#### Search Profiles
- Item details (make, model, color, size)
- Unique features and descriptions
- Search parameters and location
- Owner contact information

#### Listings
- Marketplace listing details
- Extracted content (title, description, price)
- Images and metadata
- Processing status

#### Analysis Results
- AI match scores and reasoning
- Confidence levels and recommendations
- Model version tracking
- Notification status

### Advanced Supabase Usage

```python
from recovrr.database import get_supabase_service

# Get dashboard statistics
supabase = get_supabase_service()
stats = supabase.get_dashboard_stats()
print(f"Active profiles: {stats['active_profiles']}")
print(f"Total matches: {stats['matches_found']}")

# Search listings with full-text search
results = supabase.search_listings_by_text("cannondale road bike")

# Get analytics for a specific profile
analytics = supabase.get_profile_analytics(profile_id=1)
print(f"Average match score: {analytics['avg_match_score']}")
```

## 🔒 Security & Privacy

- **No Personal Data Storage**: Only stores necessary item details
- **Secure API Key Management**: Environment-based configuration
- **Rate Limiting**: Respectful scraping with delays
- **Error Handling**: Graceful failure recovery
- **Audit Trails**: Comprehensive logging for debugging

## 🛠️ Development

### Project Structure
```
recovrr/
├── agents/
│   ├── __init__.py
│   └── matcher_agent.py       # AI matching logic
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py        # Abstract scraper base
│   ├── ebay_scraper.py        # eBay implementation
│   ├── facebook_scraper.py    # Facebook implementation
│   └── scraper_factory.py     # Scraper management
├── database/
│   ├── __init__.py
│   ├── database.py            # Database connection
│   └── models.py              # SQLAlchemy models
├── notifications/
│   ├── __init__.py
│   ├── base_notifier.py       # Abstract notifier
│   ├── email_notifier.py      # Email implementation
│   ├── sms_notifier.py        # SMS implementation
│   └── notification_service.py # Coordination service
├── scheduler/
│   ├── __init__.py
│   ├── monitoring_job.py      # Main monitoring logic
│   └── scheduler_service.py   # Job scheduling
└── config/
    ├── __init__.py
    └── settings.py            # Configuration management
```

### Testing

The project uses simple script-based testing as per your preference. Create test scripts in a `scripts/` directory:

```python
# scripts/test_scraping.py
import asyncio
from recovrr.scrapers import EbayScraper

async def test_ebay():
    scraper = EbayScraper()
    async with scraper:
        results = await scraper.search("cannondale synapse")
        print(f"Found {len(results)} listings")

if __name__ == "__main__":
    asyncio.run(test_ebay())
```

### Adding Features

1. **New AI Models**: Extend `MatcherAgent` with different LLM providers
2. **Additional Scrapers**: Implement `BaseScraper` for new marketplaces
3. **Notification Channels**: Extend `BaseNotifier` for new services
4. **Analysis Enhancements**: Add image analysis or advanced matching logic

## 📈 Scaling Considerations

### Performance
- **Concurrent Scraping**: Configurable parallel scraper limits
- **Rate Limiting**: Built-in delays to respect site policies
- **Database Optimization**: Indexed queries and connection pooling
- **Caching**: URL deduplication and result caching

### Deployment
- **Container Ready**: Easy Docker deployment
- **Environment Separation**: Configuration-based staging/production
- **Monitoring**: Comprehensive logging and error tracking
- **Backup**: Database backup and recovery procedures

## 🚨 Important Legal & Ethical Notes

- **Respect robots.txt**: Always check and follow site scraping policies
- **Rate Limiting**: Don't overwhelm servers with requests
- **Terms of Service**: Ensure compliance with marketplace ToS
- **Data Privacy**: Only collect necessary information
- **Law Enforcement**: Work with police for stolen item recovery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the existing code style (Black formatting)
4. Add simple test scripts for new functionality
5. Submit a pull request with clear description

## 📄 License

[Add your preferred license here]

## 🆘 Support

For issues, questions, or feature requests:

1. Check existing issues in the repository
2. Create a new issue with detailed description
3. Include relevant logs and configuration (redact sensitive data)

---

**Recovrr** - Helping reunite owners with their stolen items through intelligent automation. 🔍✨
