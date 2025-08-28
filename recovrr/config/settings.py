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

    # AI/LLM settings for agents framework
    gemini_api_key: str | None = Field(default=None, description="Google Gemini API key for AI analysis")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key (alternative to Gemini)")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key (alternative to Gemini)")
    
    # AI model configuration
    default_model_name: str = Field(default="gemini-2.0-flash-001", description="Default AI model to use")
    ai_temperature: float = Field(default=0.1, description="AI temperature for consistent analysis")
    ai_max_tokens: int = Field(default=4096, description="Maximum tokens for AI responses")
    ai_top_k: int = Field(default=25, description="Top-k parameter for Gemini model")

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
