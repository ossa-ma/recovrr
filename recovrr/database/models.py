"""Database models for Recovrr."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class SearchProfile(Base):
    """Model for storing search profiles (items to monitor)."""
    
    __tablename__ = "search_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Item details
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    color = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    unique_features = Column(Text, nullable=True)
    
    # Search parameters
    location = Column(String(255), nullable=True)
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    search_terms = Column(JSON, nullable=True)  # Additional search keywords
    
    # Contact information
    owner_email = Column(String(255), nullable=False)
    owner_phone = Column(String(50), nullable=True)
    
    # Status and metadata
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    listings = relationship("AnalysisResult", back_populates="search_profile")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for AI analysis."""
        return {
            "make": self.make,
            "model": self.model,
            "color": self.color,
            "size": self.size,
            "description": self.description,
            "unique_features": self.unique_features,
            "location": self.location,
            "search_terms": self.search_terms or []
        }


class Listing(Base):
    """Model for storing marketplace listings."""
    
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    
    # Listing details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=True)
    location = Column(String(255), nullable=True)
    image_urls = Column(JSON, nullable=True)  # List of image URLs
    
    # Marketplace info
    marketplace = Column(String(100), nullable=False, index=True)
    external_id = Column(String(255), nullable=True, index=True)
    
    # Status tracking
    status = Column(String(50), default="new", nullable=False, index=True)
    # Status values: 'new', 'analyzed', 'match_found', 'ignored'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis_results = relationship("AnalysisResult", back_populates="listing")
    
    def to_dict(self) -> Dict[str, Any]:
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


class AnalysisResult(Base):
    """Model for storing AI analysis results."""
    
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    search_profile_id = Column(Integer, ForeignKey("search_profiles.id"), nullable=False)
    
    # Analysis results
    match_score = Column(Float, nullable=False, index=True)
    reasoning = Column(Text, nullable=True)
    confidence_level = Column(String(50), nullable=True)  # 'low', 'medium', 'high'
    
    # AI model info
    model_used = Column(String(100), nullable=True)
    analysis_version = Column(String(50), nullable=True)
    
    # Status and actions
    notification_sent = Column(Boolean, default=False, nullable=False)
    reviewed_by_human = Column(Boolean, default=False, nullable=False)
    is_false_positive = Column(Boolean, nullable=True)
    
    # Timestamps
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    listing = relationship("Listing", back_populates="analysis_results")
    search_profile = relationship("SearchProfile", back_populates="listings")
