"""Search profile model for stolen item details."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class SearchProfile(BaseModel):
    """Model for storing search profiles (items to monitor)."""

    id: Optional[int] = None
    name: str = Field(..., description="Name/description of the search profile")

    # Item details
    make: Optional[str] = Field(None, description="Item manufacturer")
    model: Optional[str] = Field(None, description="Specific model")
    color: Optional[str] = Field(None, description="Primary color")
    size: Optional[str] = Field(None, description="Size specification")
    description: Optional[str] = Field(None, description="General description")
    unique_features: Optional[str] = Field(None, description="Distinctive features")

    # Search parameters
    location: Optional[str] = Field(None, description="Location where item was stolen")
    price_min: Optional[float] = Field(None, description="Minimum expected price")
    price_max: Optional[float] = Field(None, description="Maximum expected price")
    search_terms: Optional[List[str]] = Field(
        default_factory=list, description="Additional search keywords"
    )

    # Contact information
    owner_email: EmailStr = Field(..., description="Owner's email address")
    owner_phone: Optional[str] = Field(None, description="Owner's phone number")

    # Status and metadata
    active: bool = Field(True, description="Whether the profile is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    def to_search_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for search operations."""
        return {
            "make": self.make,
            "model": self.model,
            "color": self.color,
            "size": self.size,
            "description": self.description,
            "unique_features": self.unique_features,
            "location": self.location,
            "search_terms": self.search_terms or [],
        }

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations (excluding None values)."""
        data = self.model_dump(exclude_none=True, exclude={"id"})
        return data
