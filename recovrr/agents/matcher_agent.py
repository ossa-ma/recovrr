"""AI Agent for matching marketplace listings to search profiles."""

import json
import logging
from typing import Any

from agents.base.agent import BaseAgent
from agents.core.abstract import (
    AbstractLLMClient,
    GenericTextContentBlock,
)
from agents.core.execution_service import ToolExecutionService
from recovrr.config.settings import settings

logger = logging.getLogger(__name__)


class MatcherAgent(BaseAgent):
    """AI Agent that analyzes marketplace listings for potential matches."""

    def __init__(
        self,
        client: AbstractLLMClient,
        model_name: str,
        execution_service: ToolExecutionService | None = None,
        **kwargs: Any,
    ):
        """Initialize the matcher agent.

        Args:
            client: The LLM client to use
            model_name: The AI model name
            execution_service: Tool execution service (not needed for this agent)
            **kwargs: Additional arguments
        """
        system_prompt = self._create_system_prompt()

        default_completion_kwargs = {
            "max_tokens": settings.ai_max_tokens,
            "temperature": settings.ai_temperature,
        }

        # Add top_k for Gemini models
        if "gemini" in model_name.lower():
            default_completion_kwargs["top_k"] = settings.ai_top_k

        super().__init__(
            client=client,
            model_name=model_name,
            execution_service=execution_service,
            system_prompt=system_prompt,
            default_completion_kwargs=default_completion_kwargs,
            **kwargs,
        )

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
        self, listing_details: dict[str, Any], search_profile: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze a listing against a search profile for potential matches.

        Args:
            listing_details: Dictionary containing listing information
            search_profile: Dictionary containing stolen item details

        Returns:
            Dictionary containing match analysis results
        """
        try:
            # Create the analysis prompt
            user_prompt_text = self._create_analysis_prompt(listing_details, search_profile)

            # Create content blocks for the framework
            content_blocks = [GenericTextContentBlock(text=user_prompt_text)]

            # Make the LLM call using the framework method
            response = await self._make_llm_call(user_content_parts=content_blocks)

            # Parse the JSON response
            result = json.loads(response.text)

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
        self, listing_details: dict[str, Any], search_profile: dict[str, Any]
    ) -> str:
        """Create the user prompt for analysis."""
        return f"""
--- STOLEN ITEM DETAILS ---
Make: {search_profile.get("make", "Unknown")}
Model: {search_profile.get("model", "Unknown")}
Color: {search_profile.get("color", "Unknown")}
Size: {search_profile.get("size", "Unknown")}
Description: {search_profile.get("description", "No description provided")}
Unique Features: {search_profile.get("unique_features", "None specified")}
Stolen Location: {search_profile.get("location", "Unknown")}
Additional Search Terms: {", ".join(search_profile.get("search_terms", []))}

--- MARKETPLACE LISTING ---
Title: {listing_details.get("title", "No title")}
Description: {listing_details.get("description", "No description")}
Price: ${listing_details.get("price", "Unknown")}
Location: {listing_details.get("location", "Unknown")}
Marketplace: {listing_details.get("marketplace", "Unknown")}
URL: {listing_details.get("url", "No URL")}
Images Available: {len(listing_details.get("image_urls", []))} images

--- ANALYSIS TASK ---
Based on the provided details, analyze the likelihood that this marketplace listing is the stolen item. 
Pay special attention to make, model, color, size, location proximity, and any unique features mentioned.
Consider the price point and seller behavior if relevant.

Provide your analysis in the required JSON format.
"""

    def _validate_response(self, result: dict[str, Any]) -> None:
        """Validate the AI response structure."""
        required_fields = [
            "match_score",
            "confidence_level",
            "reasoning",
            "key_indicators",
            "concerns",
            "recommendation",
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

    def _create_error_response(self, error_message: str) -> dict[str, Any]:
        """Create a standardized error response."""
        return {
            "match_score": 0.0,
            "confidence_level": "low",
            "reasoning": f"Analysis failed: {error_message}",
            "key_indicators": [],
            "concerns": ["Analysis error occurred"],
            "recommendation": "ignore",
        }

    def should_notify(self, analysis_result: dict[str, Any]) -> bool:
        """Determine if a notification should be sent based on analysis results.

        Args:
            analysis_result: The result from check_match()

        Returns:
            Boolean indicating whether to send notification
        """
        match_score = analysis_result.get("match_score", 0)
        recommendation = analysis_result.get("recommendation", "ignore")

        # Send notification if score exceeds threshold or high priority
        return match_score >= settings.match_threshold or recommendation == "high_priority"


def create_matcher_agent() -> MatcherAgent:
    """Factory function to create a MatcherAgent with proper LLM client setup.

    Returns:
        Configured MatcherAgent instance
    """
    from agents.llm_providers.gemini import GeminiClient

    # Setup Gemini client
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    llm_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model_name=settings.default_model_name,
        max_tokens=settings.ai_max_tokens,
    )

    # Create and return the agent
    return MatcherAgent(
        client=llm_client,
        model_name=settings.default_model_name,
        execution_service=None,  # No tools needed for this agent
    )
