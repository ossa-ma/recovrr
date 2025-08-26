"""Supabase database client following the established pattern."""

import asyncio
import contextlib
import logging
import os
from typing import List, Optional, Dict, Any

import postgrest
from supabase import AsyncClient
from supabase._async.client import AsyncClient as Client, create_client

from ..config import settings
from ..models import SearchProfile, Listing, AnalysisResult

log = logging.getLogger(__name__)


async def create_supabase(url: str, key: str) -> Client:
    """Create Supabase client."""
    return await create_client(url, key)


class SupabaseDB:
    """Main Supabase database client."""
    
    def __init__(
        self, 
        uri: str | None = None, 
        key: str | None = None
    ) -> None:
        self._uri: str = uri or settings.supabase_url
        self._key: str = key or settings.supabase_key
        self._client: AsyncClient | None = None
        self._lock = asyncio.Lock()

    @contextlib.asynccontextmanager
    async def get_client(self):
        """Retrieve a Supabase client for the given uri and key."""
        if self._client is None:
            # Prevent race conditions of two requests seeing client as None and trying to initialize it
            async with self._lock:
                if self._client is None:  # Double-check pattern
                    self._client = await create_client(
                        supabase_url=self._uri, supabase_key=self._key
                    )

        yield self._client

    @contextlib.asynccontextmanager
    async def get_table(self, table_name: str):
        """Retrieve Supabase table by table name."""
        async with self.get_client() as client:
            yield client.table(table_name)

    @contextlib.asynccontextmanager
    async def get_sql(self):
        """Retrieve Supabase SQL function.
        
        Allows us to execute predefined Supabase-hosted SQL functions through RPC.
        """
        async with self.get_client() as client:
            yield client.rpc


# Global database instance
supabase = SupabaseDB()


class SearchProfileDB:
    """Database operations for search profiles."""
    
    async def create_search_profile(self, profile_data: Dict[str, Any]) -> SearchProfile:
        """Create a new search profile."""
        async with supabase.get_table("search_profiles") as table:
            try:
                request = await table.insert(profile_data).execute()
                return SearchProfile.model_validate(request.data[0])
            except postgrest.exceptions.APIError as e:
                raise ValueError(f"Failed to create search profile: {e.details}")

    async def get_search_profile(self, profile_id: int) -> SearchProfile:
        """Get a search profile by ID."""
        async with supabase.get_table("search_profiles") as table:
            request = await table.select("*").eq("id", profile_id).execute()
            if not request.data:
                raise ValueError(f"Search profile with ID {profile_id} not found.")
            return SearchProfile.model_validate(request.data[0])

    async def get_all_search_profiles(self) -> List[SearchProfile]:
        """Get all search profiles."""
        async with supabase.get_table("search_profiles") as table:
            request = await table.select("*").execute()
            data = request.data if request.data else []
            return [SearchProfile.model_validate(d) for d in data]

    async def get_active_search_profiles(self) -> List[SearchProfile]:
        """Get all active search profiles."""
        async with supabase.get_table("search_profiles") as table:
            request = await table.select("*").eq("active", True).execute()
            data = request.data if request.data else []
            return [SearchProfile.model_validate(d) for d in data]

    async def update_search_profile(self, profile_id: int, updates: Dict[str, Any]) -> SearchProfile:
        """Update a search profile."""
        async with supabase.get_table("search_profiles") as table:
            request = await table.update(updates).eq("id", profile_id).execute()
            if not request.data:
                raise ValueError(f"Search profile with ID {profile_id} not found.")
            return SearchProfile.model_validate(request.data[0])

    async def delete_search_profile(self, profile_id: int) -> bool:
        """Delete a search profile."""
        async with supabase.get_table("search_profiles") as table:
            request = await table.delete().eq("id", profile_id).execute()
            return len(request.data) > 0

    async def get_search_profile_by_email(self, email: str) -> List[SearchProfile]:
        """Get search profiles by owner email."""
        async with supabase.get_table("search_profiles") as table:
            request = await table.select("*").eq("owner_email", email).execute()
            data = request.data if request.data else []
            return [SearchProfile.model_validate(d) for d in data]


class ListingDB:
    """Database operations for marketplace listings."""
    
    async def create_listing(self, listing_data: Dict[str, Any]) -> Listing:
        """Create a new listing."""
        async with supabase.get_table("listings") as table:
            try:
                request = await table.insert(listing_data).execute()
                return Listing.model_validate(request.data[0])
            except postgrest.exceptions.APIError as e:
                raise ValueError(f"Failed to create listing: {e.details}")

    async def get_listing(self, listing_id: int) -> Listing:
        """Get a listing by ID."""
        async with supabase.get_table("listings") as table:
            request = await table.select("*").eq("id", listing_id).execute()
            if not request.data:
                raise ValueError(f"Listing with ID {listing_id} not found.")
            return Listing.model_validate(request.data[0])

    async def get_listing_by_url(self, url: str) -> Optional[Listing]:
        """Get a listing by URL."""
        async with supabase.get_table("listings") as table:
            request = await table.select("*").eq("url", url).execute()
            if not request.data:
                return None
            return Listing.model_validate(request.data[0])

    async def get_listings_by_status(self, status: str) -> List[Listing]:
        """Get listings by status."""
        async with supabase.get_table("listings") as table:
            request = await table.select("*").eq("status", status).execute()
            data = request.data if request.data else []
            return [Listing.model_validate(d) for d in data]

    async def get_new_listings(self) -> List[Listing]:
        """Get all new listings."""
        return await self.get_listings_by_status("new")

    async def update_listing(self, listing_id: int, updates: Dict[str, Any]) -> Listing:
        """Update a listing."""
        async with supabase.get_table("listings") as table:
            request = await table.update(updates).eq("id", listing_id).execute()
            if not request.data:
                raise ValueError(f"Listing with ID {listing_id} not found.")
            return Listing.model_validate(request.data[0])

    async def bulk_update_listing_status(self, listing_ids: List[int], new_status: str) -> bool:
        """Bulk update listing statuses."""
        async with supabase.get_table("listings") as table:
            request = await table.update({"status": new_status}).in_("id", listing_ids).execute()
            return len(request.data) > 0

    async def get_existing_urls(self) -> set[str]:
        """Get all existing listing URLs for duplicate checking."""
        async with supabase.get_table("listings") as table:
            request = await table.select("url").execute()
            return {row["url"] for row in request.data} if request.data else set()

    async def search_listings_by_text(self, search_query: str, limit: int = 20) -> List[Listing]:
        """Search listings using full-text search."""
        async with supabase.get_table("listings") as table:
            request = await table.select("*").text_search("title", search_query).limit(limit).execute()
            data = request.data if request.data else []
            return [Listing.model_validate(d) for d in data]


class AnalysisResultDB:
    """Database operations for analysis results."""
    
    async def create_analysis_result(self, analysis_data: Dict[str, Any]) -> AnalysisResult:
        """Create a new analysis result."""
        async with supabase.get_table("analysis_results") as table:
            try:
                request = await table.insert(analysis_data).execute()
                return AnalysisResult.model_validate(request.data[0])
            except postgrest.exceptions.APIError as e:
                raise ValueError(f"Failed to create analysis result: {e.details}")

    async def get_analysis_result(self, result_id: int) -> AnalysisResult:
        """Get an analysis result by ID."""
        async with supabase.get_table("analysis_results") as table:
            request = await table.select("*").eq("id", result_id).execute()
            if not request.data:
                raise ValueError(f"Analysis result with ID {result_id} not found.")
            return AnalysisResult.model_validate(request.data[0])

    async def get_analysis_results_for_listing(self, listing_id: int) -> List[AnalysisResult]:
        """Get all analysis results for a listing."""
        async with supabase.get_table("analysis_results") as table:
            request = await table.select("*").eq("listing_id", listing_id).execute()
            data = request.data if request.data else []
            return [AnalysisResult.model_validate(d) for d in data]

    async def get_analysis_results_for_profile(self, profile_id: int) -> List[AnalysisResult]:
        """Get all analysis results for a search profile."""
        async with supabase.get_table("analysis_results") as table:
            request = await table.select("*").eq("search_profile_id", profile_id).execute()
            data = request.data if request.data else []
            return [AnalysisResult.model_validate(d) for d in data]

    async def get_high_confidence_matches(self, min_score: float = 7.0) -> List[AnalysisResult]:
        """Get high confidence matches."""
        async with supabase.get_table("analysis_results") as table:
            request = await table.select("*").gte("match_score", min_score).execute()
            data = request.data if request.data else []
            return [AnalysisResult.model_validate(d) for d in data]

    async def update_analysis_result(self, result_id: int, updates: Dict[str, Any]) -> AnalysisResult:
        """Update an analysis result."""
        async with supabase.get_table("analysis_results") as table:
            request = await table.update(updates).eq("id", result_id).execute()
            if not request.data:
                raise ValueError(f"Analysis result with ID {result_id} not found.")
            return AnalysisResult.model_validate(request.data[0])

    async def mark_notification_sent(self, result_id: int) -> AnalysisResult:
        """Mark an analysis result as having notification sent."""
        from datetime import datetime
        return await self.update_analysis_result(result_id, {
            "notification_sent": True,
            "notification_sent_at": datetime.now().isoformat()
        })

    async def get_profile_analytics(self, profile_id: int) -> Dict[str, Any]:
        """Get analytics for a specific search profile."""
        async with supabase.get_table("analysis_results") as table:
            request = await table.select("*").eq("search_profile_id", profile_id).execute()
            results = request.data if request.data else []
            
            if not results:
                return {
                    "total_analyses": 0,
                    "avg_match_score": 0,
                    "high_confidence_matches": 0,
                    "notifications_sent": 0
                }
            
            match_scores = [r["match_score"] for r in results]
            return {
                "total_analyses": len(results),
                "avg_match_score": sum(match_scores) / len(match_scores),
                "high_confidence_matches": len([r for r in results if r["match_score"] >= 8.0]),
                "notifications_sent": len([r for r in results if r["notification_sent"]])
            }


class DashboardDB:
    """Database operations for dashboard statistics."""
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get overall dashboard statistics."""
        stats = {}
        
        # Get total active search profiles
        async with supabase.get_table("search_profiles") as table:
            request = await table.select("id").eq("active", True).execute()
            stats["active_profiles"] = len(request.data) if request.data else 0
        
        # Get total listings
        async with supabase.get_table("listings") as table:
            request = await table.select("id").execute()
            stats["total_listings"] = len(request.data) if request.data else 0
        
        # Get matches found (high confidence)
        async with supabase.get_table("analysis_results") as table:
            request = await table.select("id").gte("match_score", 7.0).execute()
            stats["matches_found"] = len(request.data) if request.data else 0
        
        # Get recent activity (last 24 hours)
        async with supabase.get_table("listings") as table:
            request = await table.select("id").gte("created_at", "now() - interval '24 hours'").execute()
            stats["recent_listings"] = len(request.data) if request.data else 0
        
        return stats
