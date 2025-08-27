from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Model for storing AI analysis results."""
    
    id: int | None = None
    
    # Foreign keys
    listing_id: int = Field(..., description="ID of the analyzed listing")
    search_profile_id: int = Field(..., description="ID of the search profile")
    
    # Analysis results
    match_score: float = Field(..., ge=0, le=10, description="Match score (0-10)")
    reasoning: str | None = Field(None, description="AI reasoning for the score")
    confidence_level: str = Field(..., description="Confidence level (low, medium, high)")
    key_indicators: list[str] | None = Field(default_factory=list, description="Key matching indicators")
    concerns: list[str] | None = Field(default_factory=list, description="Concerns or missing info")
    recommendation: str = Field(..., description="Recommendation (investigate, ignore, high_priority)")
    
    # AI model info
    model_used: str | None = Field(None, description="AI model used for analysis")
    analysis_version: str | None = Field(None, description="Analysis algorithm version")
    
    # Status and actions
    notification_sent: bool = Field(False, description="Whether notification was sent")
    reviewed_by_human: bool = Field(False, description="Whether reviewed by human")
    is_false_positive: bool | None = Field(None, description="Human feedback on accuracy")
    
    # Timestamps
    analyzed_at: datetime | None = None
    notification_sent_at: datetime | None = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def to_db_dict(self) -> dict:
        """Convert to dictionary for database operations."""
        data = self.model_dump(exclude_none=True, exclude={"id"})
        # Ensure timestamps are properly formatted
        if self.analyzed_at:
            data['analyzed_at'] = self.analyzed_at.isoformat()
        if self.notification_sent_at:
            data['notification_sent_at'] = self.notification_sent_at.isoformat()
        return data
    
    @property
    def should_notify(self) -> bool:
        """Determine if this result should trigger a notification."""
        return (
            self.match_score >= 7.0 or 
            self.recommendation == "high_priority"
        ) and not self.notification_sent
