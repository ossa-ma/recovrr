"""Listing model for marketplace listings."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field


class Listing(BaseModel):
    """Model for storing marketplace listings."""
    
    id: Optional[int] = None
    url: str = Field(..., description="Listing URL")
    
    # Listing details
    title: str = Field(..., description="Listing title")
    description: Optional[str] = Field(None, description="Listing description")
    price: Optional[float] = Field(None, description="Listed price")
    location: Optional[str] = Field(None, description="Item location")
    image_urls: Optional[List[str]] = Field(default_factory=list, description="Image URLs")
    
    # Marketplace info
    marketplace: str = Field(..., description="Marketplace name (ebay, facebook, etc.)")
    external_id: Optional[str] = Field(None, description="External marketplace ID")
    
    # Status tracking
    status: str = Field("new", description="Processing status")
    # Status values: 'new', 'analyzed', 'match_found', 'ignored'
    
    # Timestamps
    created_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def to_analysis_dict(self) -> Dict[str, Any]:
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
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations (excluding None values)."""
        data = self.model_dump(exclude_none=True, exclude={"id"})
        # Ensure timestamps are properly formatted
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.scraped_at:
            data['scraped_at'] = self.scraped_at.isoformat()
        return data
