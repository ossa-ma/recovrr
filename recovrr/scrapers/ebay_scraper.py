"""eBay marketplace scraper."""

import logging
from typing import Any
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from recovrr.models.listing import Listing

logger = logging.getLogger(__name__)


class EbayScraper(BaseScraper):
    """Scraper for eBay marketplace."""
    
    def __init__(self):
        """Initialize eBay scraper."""
        super().__init__("ebay")
        self.base_url = "https://www.ebay.com"
        self.search_url = f"{self.base_url}/sch/i.html"
        
    async def search(self, search_terms: str, location: str | None = None) -> list[Listing]:
        """Search eBay for items.
        
        Args:
            search_terms: Search query
            location: Optional location filter
            
        Returns:
            List of standardized listing objects
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
            response = await self.session.get(url)
            if response.status_code != 200:
                logger.error(f"eBay search failed with status {response.status_code}")
                return []
                
            html = response.text
                
            # Parse results
            return self._parse_search_results(html)
            
        except Exception as e:
            logger.error(f"Error searching eBay: {e}")
            return []
            
    def _parse_search_results(self, html: str) -> list[Listing]:
        """Parse eBay search results page.
        
        Args:
            html: HTML content of search results page
            
        Returns:
            List of standardized listing objects
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find listing containers (updated for new eBay structure)
        listing_elements = soup.find_all('li', {'class': 's-card'})
        
        for element in listing_elements:
            try:
                listing = self._parse_listing(element)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.warning(f"Error parsing eBay listing: {e}")
                continue
                
        return listings
        
    def _parse_listing(self, listing_element) -> Listing | None:
        """Parse a single eBay listing.
        
        Args:
            listing_element: BeautifulSoup element containing listing
            
        Returns:
            Standardized listing object or None
        """
        try:
            # Extract title
            title_elem = listing_element.find('span', {'class': 'su-styled-text primary default'})
            if not title_elem:
                return None
            title = self._clean_text(title_elem.get_text())
            
            # Extract URL
            link_elem = listing_element.find('a', class_='su-card-container__header')
            if not link_elem or not link_elem.get('href'):
                return None
            url = link_elem['href']
            
            # Extract external ID from URL (eBay item ID)
            external_id = url.split('/itm/')[-1].split('?')[0] if '/itm/' in url else url.split('/')[-1]
            
            # Extract price
            price_elem = listing_element.find('span', {'class': 'su-styled-text primary bold medium s-card__price'}) or \
                        listing_element.find('span', {'class': 'su-styled-text primary italic medium s-card__price'})
            price = None
            if price_elem:
                price = self._clean_price(price_elem.get_text())
                
            # Extract location
            location = "Location not specified"
            for span in listing_element.find_all('span', {'class': 'su-styled-text secondary small'}):
                text = span.get_text()
                if 'Located in' in text:
                    location = self._clean_text(text)
                    break
                    
            # Extract image
            images = []
            img_elem = listing_element.find('img', {'class': 's-card__image'})
            if img_elem and img_elem.get('src'):
                images.append(img_elem['src'])
                
            # Extract condition/description
            condition_elem = listing_element.find('span', {'class': 'su-styled-text secondary default'})
            description = condition_elem.get_text() if condition_elem else ""
            
            # Create clean Listing object
            return Listing(
                external_id=external_id,
                source="ebay",
                title=title,
                price=price,
                location=location,
                url=url,
                description=description,
                images=images,
                currency="USD"
            )
            
        except Exception as e:
            logger.warning(f"Error parsing eBay listing element: {e}")
            return None
            
    async def get_listing_details(self, listing_url: str) -> dict[str, Any] | None:
        """Get detailed information for a specific listing.
        
        Args:
            listing_url: URL of the listing
            
        Returns:
            Detailed listing information or None
        """
        try:
            await self._rate_limit()
            
            response = await self.session.get(listing_url)
            if response.status_code != 200:
                return None
                
            html = response.text
                
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
