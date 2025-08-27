"""AI Agent for matching marketplace listings to search profiles."""

import json
import logging
from typing import Dict, Any

from agents.base.agent import BaseAgent
from recovrr.config.settings import settings

logger = logging.getLogger(__name__)


class MatcherAgent(BaseAgent):
    """AI Agent that analyzes marketplace listings for potential matches."""
    
    def __init__(self, model_name: str = "anthropic/claude-3-5-sonnet-20241022"):
        """Initialize the matcher agent.
        
        Args:
            model_name: The AI model to use for analysis
        """
        super().__init__(model_name=model_name)
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the matching analysis."""
        return """You are an expert assistant specialized in identifying stolen items on marketplaces. 

Your task is to analyze marketplace listings and determine if they match descriptions of stolen items. You must be thorough but avoid false positives that could waste someone's time.

Key analysis factors:
1. **Make and Model**: Exact or close matches are strong indicators
2. **Physical Characteristics**: Color, size, condition details
3. **Unique Features**: Scratches, modifications, distinctive markings
4. **Location**: Geographic proximity to where item was stolen
5. **Price**: Unusually low prices might indicate stolen goods
6. **Seller Behavior**: Vague descriptions, poor photos, urgency to sell
7. **Timeline**: Recently listed items after theft date

Scoring Guidelines:
- 9-10: Very high confidence match (multiple strong indicators)
- 7-8: High confidence (several good indicators)
- 5-6: Moderate confidence (some indicators but missing key details)
- 3-4: Low confidence (few weak indicators)
- 1-2: Very low confidence (minimal similarity)
- 0: No match

Always provide your response in this exact JSON format:
{
    "match_score": <float between 0-10>,
    "confidence_level": "<low|medium|high>",
    "reasoning": "<detailed explanation of your analysis>",
    "key_indicators": ["<list of specific matching factors>"],
    "concerns": ["<list of potential issues or missing information>"],
    "recommendation": "<investigate|ignore|high_priority>"
}"""

    async def check_match(
        self, 
        listing_details: Dict[str, Any], 
        search_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a listing against a search profile for potential matches.
        
        Args:
            listing_details: Dictionary containing listing information
            search_profile: Dictionary containing stolen item details
            
        Returns:
            Dictionary containing match analysis results
        """
        try:
            # Create the analysis prompt
            user_prompt = self._create_analysis_prompt(listing_details, search_profile)
            
            # Make the LLM call
            response = await self._make_llm_call(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.1  # Low temperature for consistent analysis
            )
            
            # Parse the JSON response
            result = json.loads(response)
            
            # Validate the response structure
            self._validate_response(result)
            
            logger.info(
                f"Analysis complete for listing {listing_details.get('url', 'unknown')}: "
                f"Score {result['match_score']}, Confidence {result['confidence_level']}"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._create_error_response("Invalid JSON response from AI model")
            
        except Exception as e:
            logger.error(f"Error in match analysis: {e}")
            return self._create_error_response(f"Analysis failed: {str(e)}")
    
    def _create_analysis_prompt(
        self, 
        listing_details: Dict[str, Any], 
        search_profile: Dict[str, Any]
    ) -> str:
        """Create the user prompt for analysis."""
        return f"""
--- STOLEN ITEM DETAILS ---
Make: {search_profile.get('make', 'Unknown')}
Model: {search_profile.get('model', 'Unknown')}
Color: {search_profile.get('color', 'Unknown')}
Size: {search_profile.get('size', 'Unknown')}
Description: {search_profile.get('description', 'No description provided')}
Unique Features: {search_profile.get('unique_features', 'None specified')}
Stolen Location: {search_profile.get('location', 'Unknown')}
Additional Search Terms: {', '.join(search_profile.get('search_terms', []))}

--- MARKETPLACE LISTING ---
Title: {listing_details.get('title', 'No title')}
Description: {listing_details.get('description', 'No description')}
Price: ${listing_details.get('price', 'Unknown')}
Location: {listing_details.get('location', 'Unknown')}
Marketplace: {listing_details.get('marketplace', 'Unknown')}
URL: {listing_details.get('url', 'No URL')}
Images Available: {len(listing_details.get('image_urls', []))} images

--- ANALYSIS TASK ---
Based on the provided details, analyze the likelihood that this marketplace listing is the stolen item. 
Pay special attention to make, model, color, size, location proximity, and any unique features mentioned.
Consider the price point and seller behavior if relevant.

Provide your analysis in the required JSON format.
"""
    
    def _validate_response(self, result: Dict[str, Any]) -> None:
        """Validate the AI response structure."""
        required_fields = [
            "match_score", "confidence_level", "reasoning", 
            "key_indicators", "concerns", "recommendation"
        ]
        
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate score range
        if not (0 <= result["match_score"] <= 10):
            raise ValueError("Match score must be between 0 and 10")
        
        # Validate confidence level
        if result["confidence_level"] not in ["low", "medium", "high"]:
            raise ValueError("Confidence level must be 'low', 'medium', or 'high'")
        
        # Validate recommendation
        if result["recommendation"] not in ["investigate", "ignore", "high_priority"]:
            raise ValueError("Recommendation must be 'investigate', 'ignore', or 'high_priority'")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "match_score": 0.0,
            "confidence_level": "low",
            "reasoning": f"Analysis failed: {error_message}",
            "key_indicators": [],
            "concerns": ["Analysis error occurred"],
            "recommendation": "ignore"
        }
    
    def should_notify(self, analysis_result: Dict[str, Any]) -> bool:
        """Determine if a notification should be sent based on analysis results.
        
        Args:
            analysis_result: The result from check_match()
            
        Returns:
            Boolean indicating whether to send notification
        """
        match_score = analysis_result.get("match_score", 0)
        recommendation = analysis_result.get("recommendation", "ignore")
        
        # Send notification if score exceeds threshold or high priority
        return (
            match_score >= settings.match_threshold or 
            recommendation == "high_priority"
        )
