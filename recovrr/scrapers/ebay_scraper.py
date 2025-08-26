"""eBay marketplace scraper."""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class EbayScraper(BaseScraper):
    """Scraper for eBay marketplace."""
    
    def __init__(self):
        """Initialize eBay scraper."""
        super().__init__("ebay")
        self.base_url = "https://www.ebay.com"
        self.search_url = f"{self.base_url}/sch/i.html"
        
    async def search(self, search_terms: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search eBay for items.
        
        Args:
            search_terms: Search query
            location: Optional location filter
            
        Returns:
            List of listing dictionaries
        """
        try:
            # Build search parameters
            params = {
                '_nkw': search_terms,
                '_sacat': '0',  # All categories
                'LH_Sold': '0',  # Active listings only
                'LH_Complete': '0',  # Active listings only
                '_sop': '10'  # Sort by newest first
            }
            
            # Add location filter if provided
            if location:
                params['_fspt'] = '1'
                params['_sadis'] = '25'  # 25 mile radius
                params['_stpos'] = location
                
            # Rate limit
            await self._rate_limit()
            
            # Make request
            url = f"{self.search_url}?{urlencode(params)}"
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"eBay search failed with status {response.status}")
                    return []
                    
                html = await response.text()
                
            # Parse results
            return self._parse_search_results(html)
            
        except Exception as e:
            logger.error(f"Error searching eBay: {e}")
            return []
            
    def _parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """Parse eBay search results page.
        
        Args:
            html: HTML content of search results page
            
        Returns:
            List of parsed listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find listing containers
        listing_elements = soup.find_all('div', {'class': 's-item'})
        
        for element in listing_elements:
            try:
                listing = self._parse_listing(element)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.warning(f"Error parsing eBay listing: {e}")
                continue
                
        return listings
        
    def _parse_listing(self, listing_element) -> Optional[Dict[str, Any]]:
        """Parse a single eBay listing.
        
        Args:
            listing_element: BeautifulSoup element containing listing
            
        Returns:
            Parsed listing dictionary or None
        """
        try:
            # Extract title
            title_elem = listing_element.find('h3', {'class': 's-item__title'})
            if not title_elem:
                return None
            title = self._clean_text(title_elem.get_text())
            
            # Extract URL
            link_elem = listing_element.find('a', {'class': 's-item__link'})
            if not link_elem or not link_elem.get('href'):
                return None
            url = link_elem['href'].split('?')[0]  # Remove parameters
            
            # Extract price
            price_elem = listing_element.find('span', {'class': 's-item__price'})
            price = None
            if price_elem:
                price_text = price_elem.get_text()
                price = self._clean_price(price_text)
                
            # Extract location
            location_elem = listing_element.find('span', {'class': 's-item__location'})
            location = None
            if location_elem:
                location = self._clean_text(location_elem.get_text())
                
            # Extract image URL
            img_elem = listing_element.find('img', {'class': 's-item__image'})
            image_urls = []
            if img_elem and img_elem.get('src'):
                image_urls = [img_elem['src']]
                
            # Extract condition/description (if available in search results)
            condition_elem = listing_element.find('span', {'class': 'SECONDARY_INFO'})
            description = ""
            if condition_elem:
                description = self._clean_text(condition_elem.get_text())
                
            # Build listing dictionary
            listing = {
                'title': title,
                'url': url,
                'price': price,
                'location': location,
                'description': description,
                'image_urls': image_urls,
                'marketplace': self.marketplace_name
            }
            
            return listing
            
        except Exception as e:
            logger.warning(f"Error parsing eBay listing element: {e}")
            return None
            
    async def get_listing_details(self, listing_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific listing.
        
        Args:
            listing_url: URL of the listing
            
        Returns:
            Detailed listing information or None
        """
        try:
            await self._rate_limit()
            
            async with self.session.get(listing_url) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract detailed description
            desc_elem = soup.find('div', {'id': 'viTabs_0_is'})
            description = ""
            if desc_elem:
                description = self._clean_text(desc_elem.get_text())
                
            # Extract all image URLs
            image_urls = []
            img_elements = soup.find_all('img', {'id': lambda x: x and 'icImg' in x})
            for img in img_elements:
                if img.get('src'):
                    image_urls.append(img['src'])
                    
            # Extract seller information
            seller_elem = soup.find('span', {'class': 'mbg-nw'})
            seller_info = ""
            if seller_elem:
                seller_info = self._clean_text(seller_elem.get_text())
                
            return {
                'description': description,
                'image_urls': image_urls,
                'seller_info': seller_info
            }
            
        except Exception as e:
            logger.error(f"Error getting eBay listing details: {e}")
            return None
