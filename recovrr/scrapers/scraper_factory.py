"""Factory for creating marketplace scrapers."""

import logging
from typing import Dict, Type, List

from .base_scraper import BaseScraper
from .ebay_scraper import EbayScraper
from .facebook_scraper import FacebookScraper

logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory class for creating and managing marketplace scrapers."""
    
    _scrapers: Dict[str, Type[BaseScraper]] = {
        'ebay': EbayScraper,
        'facebook': FacebookScraper,
    }
    
    @classmethod
    def get_scraper(cls, marketplace: str) -> BaseScraper:
        """Get a scraper instance for the specified marketplace.
        
        Args:
            marketplace: Name of the marketplace ('ebay', 'facebook', etc.)
            
        Returns:
            Scraper instance
            
        Raises:
            ValueError: If marketplace is not supported
        """
        marketplace = marketplace.lower()
        
        if marketplace not in cls._scrapers:
            raise ValueError(f"Unsupported marketplace: {marketplace}")
            
        scraper_class = cls._scrapers[marketplace]
        return scraper_class()
        
    @classmethod
    def get_available_marketplaces(cls) -> list[str]:
        """Get list of available marketplace names.
        
        Returns:
            List of marketplace names
        """
        return list(cls._scrapers.keys())
        
    @classmethod
    def register_scraper(cls, marketplace: str, scraper_class: Type[BaseScraper]):
        """Register a new scraper class.
        
        Args:
            marketplace: Name of the marketplace
            scraper_class: Scraper class that inherits from BaseScraper
        """
        if not issubclass(scraper_class, BaseScraper):
            raise ValueError("Scraper class must inherit from BaseScraper")
            
        cls._scrapers[marketplace.lower()] = scraper_class
        logger.info(f"Registered scraper for marketplace: {marketplace}")
        
    @classmethod
    async def create_all_scrapers(cls) -> List[BaseScraper]:
        """Create instances of all available scrapers.
        
        Returns:
            List of scraper instances
        """
        scrapers = []
        
        for marketplace in cls._scrapers:
            try:
                scraper = cls.get_scraper(marketplace)
                scrapers.append(scraper)
            except Exception as e:
                logger.error(f"Failed to create scraper for {marketplace}: {e}")
                
        return scrapers
