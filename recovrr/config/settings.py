from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables automatically."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="forbid"
    )

    # Supabase Database settings
    supabase_url: str = Field(description="Supabase project URL")
    supabase_key: str = Field(description="Supabase anon/service role key")

    # AI/LLM settings (handled by agents framework)
    openai_api_key: str = Field(description="OpenAI API key to be passed to Agents framework")
    anthropic_api_key: str = Field(description="Anthropic API key to be passed to Agents framework")

    # Notification settings
    sendgrid_api_key: str | None = Field(
        default=None, description="SendGrid API key for email notifications"
    )
    twilio_account_sid: str | None = Field(
        default=None, description="Twilio Account SID for SMS notifications"
    )
    twilio_auth_token: str | None = Field(
        default=None, description="Twilio Auth Token for SMS notifications"
    )
    twilio_phone_number: str | None = Field(
        default=None, description="Twilio phone number for sending SMS"
    )

    # Scraping settings
    scrape_interval_minutes: int = Field(
        default=15, description="Interval between scraping runs in minutes"
    )
    max_concurrent_scrapers: int = Field(
        default=3, description="Maximum number of concurrent scraper instances"
    )
    request_delay_seconds: float = Field(
        default=1.0, description="Delay between requests to avoid rate limiting"
    )

    # Analysis settings
    match_threshold: float = Field(
        default=7.0, description="Minimum match score to trigger notification (0-10)"
    )

    # Application settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")


# Global settings instance
settings = Settings()
