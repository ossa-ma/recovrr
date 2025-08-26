"""Facebook Marketplace scraper using curl-cffi for stealth."""

import logging
from typing import List, Dict, Any, Optional
import asyncio
import json
import re
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FacebookScraper(BaseScraper):
    """Scraper for Facebook Marketplace using curl-cffi with browser impersonation."""
    
    def __init__(self):
        """Initialize Facebook Marketplace scraper."""
        super().__init__("facebook")
        self.base_url = "https://www.facebook.com"
    
    async def start_session(self):
        """Start HTTP session with enhanced browser impersonation."""
        await super().start_session()
        
        # Additional headers to mimic real browser behavior
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
            
    async def search(self, search_terms: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search Facebook Marketplace for items.
        
        Args:
            search_terms: Search query
            location: Optional location filter
            
        Returns:
            List of listing dictionaries
        """
        try:
            # Rate limit
            await self._rate_limit()
            
            # Build search URL - Facebook Marketplace search
            params = {
                'query': search_terms,
                'sortBy': 'creation_time_descend',  # Newest first
                'exact': 'false'
            }
            
            if location:
                # Facebook uses different location parameters, this is a simplified approach
                params['location'] = location
            
            search_url = f"{self.base_url}/marketplace/search/?{urlencode(params)}"
            
            # Make request
            response = await self.session.get(search_url)
            if response.status_code != 200:
                logger.error(f"Facebook search failed with status {response.status_code}")
                return []
                
            html = response.text
            
            # Parse results
            return self._parse_search_results(html)
            
        except Exception as e:
            logger.error(f"Error searching Facebook Marketplace: {e}")
            return []
            
    def _parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """Parse Facebook Marketplace search results.
        
        Args:
            html: HTML content of search results page
            
        Returns:
            List of parsed listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        try:
            # Facebook's marketplace uses dynamic class names, so we look for patterns
            # This is a simplified approach - Facebook's actual structure is complex
            
            # Look for marketplace item containers (these selectors may need adjustment)
            listing_elements = soup.find_all('div', {'data-testid': 'marketplace-item'}) or \
                             soup.find_all('a', href=re.compile(r'/marketplace/item/\d+'))
            
            for element in listing_elements:
                try:
                    listing = self._parse_listing(element)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.warning(f"Error parsing Facebook listing: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing Facebook search results: {e}")
            
        return listings
        
    def _parse_listing(self, listing_element) -> Optional[Dict[str, Any]]:
        """Parse a single Facebook Marketplace listing.
        
        Args:
            listing_element: BeautifulSoup element containing listing
            
        Returns:
            Parsed listing dictionary or None
        """
        try:
            # Extract URL first
            link_elem = listing_element.find('a', href=re.compile(r'/marketplace/item/\d+'))
            if not link_elem:
                return None
            relative_url = link_elem.get('href')
            url = f"https://www.facebook.com{relative_url}" if relative_url.startswith('/') else relative_url
            
            # Extract title
            title_elem = listing_element.find('span', dir="auto") or \
                        listing_element.find('div', string=True)
            if not title_elem:
                return None
            title = self._clean_text(title_elem.get_text() if hasattr(title_elem, 'get_text') else str(title_elem))
            
            # Extract price (look for currency symbols)
            price = None
            price_patterns = [
                r'\$[\d,]+(?:\.\d{2})?',  # $100 or $1,000.00
                r'£[\d,]+(?:\.\d{2})?',  # £100
                r'€[\d,]+(?:\.\d{2})?'   # €100
            ]
            
            text_content = listing_element.get_text()
            for pattern in price_patterns:
                price_match = re.search(pattern, text_content)
                if price_match:
                    price = self._clean_price(price_match.group())
                    break
                    
            # Extract location (simplified - Facebook location parsing is complex)
            location = None
            location_keywords = ['mile', 'km', 'away', 'from']
            for text_elem in listing_element.find_all(string=True):
                if any(keyword in text_elem.lower() for keyword in location_keywords):
                    location = self._clean_text(text_elem)
                    break
                    
            # Extract image URL
            image_urls = []
            img_elem = listing_element.find('img')
            if img_elem and img_elem.get('src'):
                image_urls = [img_elem['src']]
                    
            # Build listing dictionary
            listing = {
                'title': title,
                'url': url,
                'price': price,
                'location': location,
                'description': "",  # Description requires visiting individual listing
                'image_urls': image_urls,
                'marketplace': self.marketplace_name
            }
            
            return listing
            
        except Exception as e:
            logger.warning(f"Error parsing Facebook listing element: {e}")
            return None
            
    async def get_listing_details(self, listing_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific Facebook listing.
        
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
            
            # Extract detailed description (Facebook structure varies)
            description = ""
            description_selectors = [
                '[data-testid="marketplace-pdp-description"]',
                'div[dir="auto"]',
                'span[dir="auto"]'
            ]
            
            for selector in description_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem and desc_elem.get_text().strip():
                    description = self._clean_text(desc_elem.get_text())
                    break
                    
            # Extract additional images
            image_urls = []
            img_elements = soup.find_all('img')
            for img in img_elements:
                img_src = img.get('src')
                if img_src and ('scontent' in img_src or 'fbcdn' in img_src):  # Facebook CDN images
                    image_urls.append(img_src)
                    
            return {
                'description': description,
                'image_urls': image_urls[:10]  # Limit to 10 images
            }
            
        except Exception as e:
            logger.error(f"Error getting Facebook listing details: {e}")
            return None
