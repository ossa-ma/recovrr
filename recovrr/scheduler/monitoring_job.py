"""Main monitoring job that orchestrates scraping and analysis."""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_session, SearchProfile, Listing, AnalysisResult
from ..scrapers import ScraperFactory
from ..agents import MatcherAgent
from ..notifications import NotificationService

logger = logging.getLogger(__name__)


class MonitoringJob:
    """Main job that orchestrates the monitoring process."""
    
    def __init__(self):
        """Initialize the monitoring job."""
        self.notification_service = NotificationService()
        self.matcher_agent = MatcherAgent()
        
    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a complete monitoring cycle.
        
        Returns:
            Summary of the monitoring cycle results
        """
        start_time = datetime.now()
        logger.info("Starting monitoring cycle")
        
        try:
            # Get active search profiles
            with get_session() as db:
                search_profiles = db.query(SearchProfile).filter(SearchProfile.active == True).all()
                
            if not search_profiles:
                logger.info("No active search profiles found")
                return {
                    'status': 'completed',
                    'search_profiles': 0,
                    'new_listings': 0,
                    'matches_found': 0,
                    'notifications_sent': 0,
                    'duration_seconds': (datetime.now() - start_time).total_seconds()
                }
                
            logger.info(f"Found {len(search_profiles)} active search profiles")
            
            # Run scraping for all profiles
            new_listings = await self._scrape_all_profiles(search_profiles)
            logger.info(f"Found {len(new_listings)} new listings")
            
            # Analyze new listings
            matches_found, notifications_sent = await self._analyze_listings(new_listings, search_profiles)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            summary = {
                'status': 'completed',
                'search_profiles': len(search_profiles),
                'new_listings': len(new_listings),
                'matches_found': matches_found,
                'notifications_sent': notifications_sent,
                'duration_seconds': duration,
                'timestamp': end_time.isoformat()
            }
            
            logger.info(f"Monitoring cycle completed: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }
            
    async def _scrape_all_profiles(self, search_profiles: List[SearchProfile]) -> List[Dict[str, Any]]:
        """Scrape all marketplaces for all search profiles.
        
        Args:
            search_profiles: List of active search profiles
            
        Returns:
            List of new listings found
        """
        all_new_listings = []
        
        # Get all available scrapers
        available_marketplaces = ScraperFactory.get_available_marketplaces()
        
        # Track existing URLs to avoid duplicates
        with get_session() as db:
            existing_urls = set(
                url[0] for url in db.query(Listing.url).all()
            )
            
        # Limit concurrent scrapers to avoid overwhelming sites
        semaphore = asyncio.Semaphore(settings.max_concurrent_scrapers)
        
        async def scrape_profile_marketplace(profile: SearchProfile, marketplace: str):
            """Scrape a specific marketplace for a specific profile."""
            async with semaphore:
                try:
                    scraper = ScraperFactory.get_scraper(marketplace)
                    async with scraper:
                        listings = await scraper.scrape_search_profile(profile.to_dict())
                        
                        # Filter out duplicates
                        new_listings = []
                        for listing in listings:
                            if not scraper.is_duplicate_url(listing['url'], existing_urls):
                                new_listings.append(listing)
                                existing_urls.add(listing['url'])
                                
                        return new_listings
                        
                except Exception as e:
                    logger.error(f"Error scraping {marketplace} for profile {profile.id}: {e}")
                    return []
                    
        # Create tasks for all profile-marketplace combinations
        tasks = []
        for profile in search_profiles:
            for marketplace in available_marketplaces:
                task = scrape_profile_marketplace(profile, marketplace)
                tasks.append(task)
                
        # Run all scraping tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all new listings
        for result in results:
            if isinstance(result, list):
                all_new_listings.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping task failed: {result}")
                
        # Save new listings to database
        if all_new_listings:
            await self._save_new_listings(all_new_listings)
            
        return all_new_listings
        
    async def _save_new_listings(self, listings: List[Dict[str, Any]]):
        """Save new listings to the database.
        
        Args:
            listings: List of listing dictionaries
        """
        try:
            with get_session() as db:
                for listing_data in listings:
                    listing = Listing(
                        url=listing_data['url'],
                        title=listing_data['title'],
                        description=listing_data.get('description', ''),
                        price=listing_data.get('price'),
                        location=listing_data.get('location'),
                        image_urls=listing_data.get('image_urls', []),
                        marketplace=listing_data['marketplace'],
                        status='new'
                    )
                    db.add(listing)
                    
                db.commit()
                logger.info(f"Saved {len(listings)} new listings to database")
                
        except Exception as e:
            logger.error(f"Error saving listings to database: {e}")
            
    async def _analyze_listings(
        self, 
        new_listings: List[Dict[str, Any]], 
        search_profiles: List[SearchProfile]
    ) -> tuple[int, int]:
        """Analyze new listings against search profiles.
        
        Args:
            new_listings: List of new listings to analyze
            search_profiles: List of search profiles to match against
            
        Returns:
            Tuple of (matches_found, notifications_sent)
        """
        matches_found = 0
        notifications_sent = 0
        
        for listing_data in new_listings:
            for profile in search_profiles:
                try:
                    # Run AI analysis
                    analysis_result = await self.matcher_agent.check_match(
                        listing_data, profile.to_dict()
                    )
                    
                    # Save analysis result to database
                    with get_session() as db:
                        # Get the saved listing
                        listing = db.query(Listing).filter(Listing.url == listing_data['url']).first()
                        if not listing:
                            continue
                            
                        # Create analysis result record
                        analysis = AnalysisResult(
                            listing_id=listing.id,
                            search_profile_id=profile.id,
                            match_score=analysis_result['match_score'],
                            reasoning=analysis_result['reasoning'],
                            confidence_level=analysis_result['confidence_level'],
                            model_used=self.matcher_agent.model_name,
                            analyzed_at=datetime.now()
                        )
                        db.add(analysis)
                        
                        # Update listing status
                        if analysis_result['match_score'] >= settings.match_threshold:
                            listing.status = 'match_found'
                            matches_found += 1
                        else:
                            listing.status = 'analyzed'
                            
                        db.commit()
                        
                    # Send notification if needed
                    if self.matcher_agent.should_notify(analysis_result):
                        try:
                            notification_results = await self.notification_service.send_match_alert(
                                profile.to_dict(), listing_data, analysis_result
                            )
                            
                            # Update notification status in database
                            if any(notification_results.values()):
                                with get_session() as db:
                                    analysis_record = db.query(AnalysisResult).filter(
                                        AnalysisResult.listing_id == listing.id,
                                        AnalysisResult.search_profile_id == profile.id
                                    ).first()
                                    if analysis_record:
                                        analysis_record.notification_sent = True
                                        analysis_record.notification_sent_at = datetime.now()
                                        db.commit()
                                        
                                notifications_sent += 1
                                logger.info(f"Notification sent for match: {listing_data['url']}")
                                
                        except Exception as e:
                            logger.error(f"Error sending notification: {e}")
                            
                except Exception as e:
                    logger.error(f"Error analyzing listing {listing_data.get('url', 'unknown')}: {e}")
                    
        return matches_found, notifications_sent
