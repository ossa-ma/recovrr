"""Database operations using Supabase direct client approach."""

from .supabase_db import (
    supabase,
    SearchProfileDB,
    ListingDB, 
    AnalysisResultDB,
    DashboardDB
)

# Create database service instances
search_profile_db = SearchProfileDB()
listing_db = ListingDB()
analysis_result_db = AnalysisResultDB()
dashboard_db = DashboardDB()

__all__ = [
    "supabase",
    "search_profile_db",
    "listing_db", 
    "analysis_result_db",
    "dashboard_db",
    "SearchProfileDB",
    "ListingDB",
    "AnalysisResultDB", 
    "DashboardDB"
]