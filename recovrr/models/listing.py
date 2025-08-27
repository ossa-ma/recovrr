from datetime import datetime
from typing import Any
from pydantic import BaseModel, HttpUrl, Field


class Listing(BaseModel):
    """Model for storing marketplace listings."""
    
    id: int | None = None
    url: str = Field(..., description="Listing URL")
    
    # Listing details
    title: str = Field(..., description="Listing title")
    description: str | None = Field(None, description="Listing description")
    price: float | None = Field(None, description="Listed price")
    location: str | None = Field(None, description="Item location")
    image_urls: list[str] | None = Field(default_factory=list, description="Image URLs")
    
    # Marketplace info
    marketplace: str = Field(..., description="Marketplace name (ebay, facebook, etc.)")
    external_id: str | None = Field(None, description="External marketplace ID")
    
    # Status tracking
    status: str = Field("new", description="Processing status")
    # Status values: 'new', 'analyzed', 'match_found', 'ignored'
    
    # Timestamps
    created_at: datetime | None = None
    scraped_at: datetime | None = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def to_analysis_dict(self) -> dict[str, Any]:
        """Convert to dictionary for AI analysis."""
        return {
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "location": self.location,
            "marketplace": self.marketplace,
            "url": self.url,
            "image_urls": self.image_urls or []
        }
    
    def to_db_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database operations (excluding None values)."""
        data = self.model_dump(exclude_none=True, exclude={"id"})
        # Ensure timestamps are properly formatted
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.scraped_at:
            data['scraped_at'] = self.scraped_at.isoformat()
        return data
