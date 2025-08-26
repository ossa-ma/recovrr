"""Facebook Marketplace scraper using browser automation."""

import logging
from typing import List, Dict, Any, Optional
import asyncio

from playwright.async_api import async_playwright, Page, Browser

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FacebookScraper(BaseScraper):
    """Scraper for Facebook Marketplace using browser automation."""
    
    def __init__(self):
        """Initialize Facebook Marketplace scraper."""
        super().__init__("facebook")
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def start_session(self):
        """Start browser session."""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser in headless mode
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                ]
            )
            
            # Create page with realistic viewport
            self.page = await self.browser.new_page(
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Set user agent
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            logger.info("Facebook scraper browser session started")
            
        except Exception as e:
            logger.error(f"Failed to start Facebook scraper session: {e}")
            raise
            
    async def close_session(self):
        """Close browser session."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
                
            logger.info("Facebook scraper browser session closed")
            
        except Exception as e:
            logger.error(f"Error closing Facebook scraper session: {e}")
            
    async def search(self, search_terms: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search Facebook Marketplace for items.
        
        Args:
            search_terms: Search query
            location: Optional location filter
            
        Returns:
            List of listing dictionaries
        """
        try:
            if not self.page:
                raise RuntimeError("Browser session not started")
                
            # Navigate to Facebook Marketplace
            marketplace_url = "https://www.facebook.com/marketplace"
            await self.page.goto(marketplace_url, wait_until="networkidle")
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Handle potential login/cookie banners
            await self._handle_popups()
            
            # Perform search
            search_box = await self.page.wait_for_selector('input[placeholder*="Search Marketplace"]', timeout=10000)
            await search_box.fill(search_terms)
            await search_box.press("Enter")
            
            # Wait for results to load
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Parse results
            listings = await self._parse_search_results()
            
            logger.info(f"Found {len(listings)} listings on Facebook Marketplace")
            return listings
            
        except Exception as e:
            logger.error(f"Error searching Facebook Marketplace: {e}")
            return []
            
    async def _handle_popups(self):
        """Handle login prompts and cookie banners."""
        try:
            # Try to close any popups/modals
            close_buttons = [
                'button[aria-label="Close"]',
                'div[role="button"]:has-text("Not Now")',
                'div[role="button"]:has-text("Cancel")',
                'button:has-text("Close")'
            ]
            
            for selector in close_buttons:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=2000)
                    if button:
                        await button.click()
                        await asyncio.sleep(1)
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"No popups to handle: {e}")
            
    async def _parse_search_results(self) -> List[Dict[str, Any]]:
        """Parse Facebook Marketplace search results.
        
        Returns:
            List of parsed listings
        """
        listings = []
        
        try:
            # Wait for listing containers to load
            await self.page.wait_for_selector('[data-testid="marketplace-item"]', timeout=10000)
            
            # Get all listing elements
            listing_elements = await self.page.query_selector_all('[data-testid="marketplace-item"]')
            
            for element in listing_elements:
                try:
                    listing = await self._parse_listing(element)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.warning(f"Error parsing Facebook listing: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing Facebook search results: {e}")
            
        return listings
        
    async def _parse_listing(self, listing_element) -> Optional[Dict[str, Any]]:
        """Parse a single Facebook Marketplace listing.
        
        Args:
            listing_element: Playwright element containing listing
            
        Returns:
            Parsed listing dictionary or None
        """
        try:
            # Extract title
            title_elem = await listing_element.query_selector('span[dir="auto"]')
            if not title_elem:
                return None
            title = await title_elem.inner_text()
            title = self._clean_text(title)
            
            # Extract URL
            link_elem = await listing_element.query_selector('a[href*="/marketplace/item/"]')
            if not link_elem:
                return None
            relative_url = await link_elem.get_attribute('href')
            url = f"https://www.facebook.com{relative_url}" if relative_url.startswith('/') else relative_url
            
            # Extract price
            price_elem = await listing_element.query_selector('span:has-text("$")')
            price = None
            if price_elem:
                price_text = await price_elem.inner_text()
                price = self._clean_price(price_text)
                
            # Extract location
            location_elem = await listing_element.query_selector('span[dir="auto"]:not(:has(span))')
            location = None
            if location_elem:
                location_text = await location_elem.inner_text()
                if any(keyword in location_text.lower() for keyword in ['mile', 'km', 'away']):
                    location = self._clean_text(location_text)
                    
            # Extract image URL
            img_elem = await listing_element.query_selector('img')
            image_urls = []
            if img_elem:
                img_src = await img_elem.get_attribute('src')
                if img_src:
                    image_urls = [img_src]
                    
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
            if not self.page:
                return None
                
            await self.page.goto(listing_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Extract detailed description
            description_selectors = [
                '[data-testid="marketplace-pdp-description"] span',
                'div[dir="auto"]:has-text("Description")',
                'span[dir="auto"]'
            ]
            
            description = ""
            for selector in description_selectors:
                try:
                    desc_elem = await self.page.wait_for_selector(selector, timeout=3000)
                    if desc_elem:
                        description = await desc_elem.inner_text()
                        description = self._clean_text(description)
                        break
                except:
                    continue
                    
            # Extract additional images
            image_urls = []
            img_elements = await self.page.query_selector_all('img[data-imgperflogname]')
            for img in img_elements:
                img_src = await img.get_attribute('src')
                if img_src and 'scontent' in img_src:  # Facebook CDN images
                    image_urls.append(img_src)
                    
            return {
                'description': description,
                'image_urls': image_urls[:10]  # Limit to 10 images
            }
            
        except Exception as e:
            logger.error(f"Error getting Facebook listing details: {e}")
            return None
