import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any
import time

from curl_cffi import requests
from recovrr.config.settings import settings

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for marketplace scrapers."""
    
    def __init__(self, marketplace_name: str):
        """Initialize the scraper.
        
        Args:
            marketplace_name: Name of the marketplace (e.g., 'ebay', 'facebook')
        """
        self.marketplace_name = marketplace_name
        self.session: requests.AsyncSession | None = None
        self.last_request_time = 0.0
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
        
    async def start_session(self):
        """Start the HTTP session with browser impersonation."""
        if self.session is None:
            # Use curl-cffi with browser impersonation to bypass anti-bot measures
            self.session = requests.AsyncSession(
                impersonate="safari_ios",  # Impersonate Safari on iOS to avoid 429s
                timeout=30
            )
            
    async def close_session(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()  # curl-cffi doesn't use await for close
            self.session = None
            
    async def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < settings.request_delay_seconds:
            await asyncio.sleep(settings.request_delay_seconds - time_since_last)
            
        self.last_request_time = time.time()
        
    @abstractmethod
    async def search(self, search_terms: str, location: str | None = None) -> list[Any]:
        """Search for items on the marketplace.
        
        Args:
            search_terms: Search query string
            location: Optional location filter
            
        Returns:
            List of Listing objects
        """
        pass
        
    @abstractmethod
    def _parse_listing(self, listing_element: Any) -> Any | None:
        """Parse a single listing from the marketplace.
        
        Args:
            listing_element: Raw listing element/data from the marketplace
            
        Returns:
            Listing object or None if parsing failed
        """
        pass
        
    def _clean_price(self, price_text: str) -> float | None:
        """Extract numeric price from price text.
        
        Args:
            price_text: Raw price text (e.g., '$25.99', '£150')
            
        Returns:
            Numeric price or None if parsing failed
        """
        if not price_text:
            return None
            
        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = price_text.replace('$', '').replace('£', '').replace('€', '')
            cleaned = cleaned.replace(',', '').replace(' ', '')
            
            # Handle price ranges (take the first price)
            if '-' in cleaned:
                cleaned = cleaned.split('-')[0]
                
            return float(cleaned)
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse price: {price_text}")
            return None
            
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Remove extra whitespace and normalize
        return ' '.join(text.strip().split())
        
    async def scrape_search_profile(self, search_profile: dict[str, Any]) -> list[Any]:
        """Scrape listings for a specific search profile.
        
        Args:
            search_profile: Search profile dictionary (from Pydantic model)
            
        Returns:
            List of Listing objects
        """
        try:
            # Build search terms from profile
            search_terms = self._build_search_terms(search_profile)
            location = search_profile.get('location')
            
            logger.info(f"Scraping {self.marketplace_name} for: {search_terms}")
            
            # Perform the search
            listings = await self.search(search_terms, location)
                
            logger.info(f"Found {len(listings)} listings on {self.marketplace_name}")
            return listings
            
        except Exception as e:
            logger.error(f"Error scraping {self.marketplace_name}: {e}")
            return []
            
    def _build_search_terms(self, search_profile: dict[str, Any]) -> str:
        """Build search query from search profile.
        
        Args:
            search_profile: Search profile dictionary
            
        Returns:
            Search query string
        """
        terms = []
        
        # Add make and model if available
        if search_profile.get('make'):
            terms.append(search_profile['make'])
        if search_profile.get('model'):
            terms.append(search_profile['model'])
            
        # Add additional search terms
        if search_profile.get('search_terms'):
            terms.extend(search_profile['search_terms'])
            
        # Join terms with spaces
        return ' '.join(terms)
        
    def is_duplicate_url(self, url: str, existing_urls: set) -> bool:
        """Check if a URL is a duplicate.
        
        Args:
            url: URL to check
            existing_urls: Set of existing URLs
            
        Returns:
            True if URL is a duplicate
        """
        # Normalize URL (remove parameters, fragments, etc.)
        normalized_url = url.split('?')[0].split('#')[0]
        return normalized_url in existing_urls
