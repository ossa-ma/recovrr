from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class Listing(BaseModel):
    """Simple, clean listing model that all scrapers return."""
    
    # Core fields that every listing must have
    external_id: str = Field(description="Unique ID from marketplace (e.g. eBay item ID)")
    source: str = Field(description="Marketplace name: 'ebay', 'facebook', 'gumtree'")
    title: str = Field(description="Listing title")
    price: float | None = Field(description="Price as float, None if not available")
    location: str = Field(description="Location text from listing")
    url: HttpUrl = Field(description="Direct URL to listing")
    
    # Optional fields with sensible defaults
    description: str = Field(default="", description="Listing description or condition")
    images: list[str] = Field(default_factory=list, description="List of image URLs")
    currency: str = Field(default="USD", description="Currency code")
    
    # Timestamps
    scraped_at: datetime = Field(default_factory=datetime.now, description="When we scraped this")
    posted_date: datetime | None = Field(default=None, description="When listing was posted")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage or API responses."""
        return {
            "external_id": self.external_id,
            "source": self.source,
            "title": self.title,
            "price": self.price,
            "location": self.location,
            "url": str(self.url),
            "description": self.description,
            "images": self.images,
            "currency": self.currency,
            "scraped_at": self.scraped_at.isoformat(),
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
        }
    
    def format_price(self) -> str:
        """Format price for display."""
        if not self.price:
            return "Price not available"
        
        symbol = "$" if self.currency == "USD" else self.currency
        return f"{symbol}{self.price:,.2f}"
    
    def get_primary_image(self) -> str | None:
        """Get the first image URL if available."""
        return self.images[0] if self.images else None
    
    def __str__(self) -> str:
        """String representation for logging."""
        return f"{self.source.upper()}: {self.title} - {self.format_price()}"


# Example of what scrapers should create:
def create_ebay_listing(item_id: str, title: str, price: float, location: str, url: str, **kwargs) -> Listing:
    """Helper to create eBay listings with consistent format."""
    return Listing(
        external_id=item_id,
        source="ebay",
        title=title,
        price=price,
        location=location,
        url=url,
        **kwargs
    )


def create_facebook_listing(post_id: str, title: str, price: float, location: str, url: str, **kwargs) -> Listing:
    """Helper to create Facebook listings with consistent format."""
    return Listing(
        external_id=post_id,
        source="facebook",
        title=title,
        price=price,
        location=location,
        url=url,
        **kwargs
    )