# Recovrr

**Marketplace Monitoring System for Stolen Item Recovery**

Recovrr automatically monitors online marketplaces for stolen items using AI analysis. It scrapes listings from multiple platforms, analyzes them against theft reports, and sends notifications when potential matches are found.

## Features

- Multi-marketplace monitoring (eBay, Facebook Marketplace)
- AI-powered listing analysis using LLMs
- Email and SMS notifications with confidence scoring
- Automated scheduling with configurable intervals
- Scalable architecture supporting multiple users

## Architecture

```
recovrr/
├── agents/          # AI agents for item matching
├── scrapers/        # Marketplace scrapers
├── database/        # Data models and Supabase integration
├── notifications/   # Email and SMS services
├── scheduler/       # Job orchestration
└── config/          # Settings management
```

## Requirements

- Python 3.13+
- `uv` package manager
- Supabase project
- OpenAI or Anthropic API key
- SendGrid API key (optional, for email)
- Twilio credentials (optional, for SMS)

## Installation

1. Clone and setup:
```bash
git clone <repository-url>
cd recovrr

# Create virtual environment
uv venv --python 3.13
source .venv/bin/activate

# Install dependencies
uv pip compile pyproject.toml -o requirements.txt
uv pip install -r requirements.txt
```

2. Configure environment:
```bash
cp env.example .env
# Edit .env with your API keys
```

3. Setup database:
```bash
# Create Supabase project at https://supabase.com
# Run migrations in Supabase SQL editor:
# - migrations/001_create_tables.sql
# - migrations/002_rls_policies.sql
# - migrations/003_dashboard_functions.sql
```

## Configuration

Required environment variables in `.env`:

```bash
# Database
SUPABASE_URL=your-project-url
SUPABASE_KEY=your-anon-key

# AI (choose one)
OPENAI_API_KEY=your-openai-key
# OR
ANTHROPIC_API_KEY=your-anthropic-key

# Notifications (optional)
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
```

## Usage

### Create Search Profile

```python
from recovrr.models.search_profile import SearchProfile
from recovrr.database.supabase import search_profile_db

profile = SearchProfile(
    name="My Stolen Bike",
    make="Trek",
    model="Domane SL 7",
    color="Blue",
    description="Road bike with carbon frame",
    owner_email="owner@example.com",
    location="San Francisco, CA"
)

# Save to database
await search_profile_db.create_search_profile(profile.to_db_dict())
```

### Start Monitoring

```python
from recovrr.scheduler.scheduler_service import SchedulerService

scheduler = SchedulerService()
scheduler.start_monitoring()
```

### Manual Testing

```bash
python test_manual.py
```

## Development

The codebase uses modern Python features:
- Python 3.13+ syntax
- Modern typing (`str | None` instead of `Optional[str]`)
- `dict` and `list` instead of `Dict` and `List`
- Pydantic models for data validation
- Direct Supabase client integration

### Key Components

- **Scrapers**: Extract listings from marketplaces using `curl-cffi` for anti-bot evasion
- **AI Agents**: Analyze listings using custom agents framework with LLM integration
- **Database**: Supabase PostgreSQL with Row Level Security
- **Notifications**: Multi-channel alerting system
- **Scheduler**: APScheduler for automated monitoring cycles

### Testing

Basic functionality test:
```bash
python test_manual.py
```

## Project Structure

- `recovrr/agents/` - AI matching logic
- `recovrr/scrapers/` - Marketplace data extraction
- `recovrr/database/` - Database operations and models
- `recovrr/notifications/` - Alert delivery systems
- `recovrr/scheduler/` - Job management
- `migrations/` - Database schema and security policies

## License

Private project for stolen item recovery assistance.