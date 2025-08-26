-- Create dashboard statistics function
CREATE OR REPLACE FUNCTION get_dashboard_stats()
RETURNS JSON AS $$
DECLARE
    stats JSON;
BEGIN
    SELECT json_build_object(
        'active_profiles', (
            SELECT COUNT(*) FROM search_profiles WHERE active = true
        ),
        'total_listings', (
            SELECT COUNT(*) FROM listings
        ),
        'matches_found', (
            SELECT COUNT(*) FROM analysis_results WHERE match_score >= 7.0
        ),
        'recent_listings', (
            SELECT COUNT(*) FROM listings 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        ),
        'high_priority_matches', (
            SELECT COUNT(*) FROM analysis_results 
            WHERE recommendation = 'high_priority'
        ),
        'notifications_sent', (
            SELECT COUNT(*) FROM analysis_results 
            WHERE notification_sent = true
        )
    ) INTO stats;
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get profile analytics
CREATE OR REPLACE FUNCTION get_profile_analytics(profile_id_param BIGINT)
RETURNS JSON AS $$
DECLARE
    analytics JSON;
BEGIN
    SELECT json_build_object(
        'total_analyses', COUNT(*),
        'avg_match_score', COALESCE(AVG(match_score), 0),
        'high_confidence_matches', COUNT(*) FILTER (WHERE match_score >= 8.0),
        'notifications_sent', COUNT(*) FILTER (WHERE notification_sent = true),
        'false_positives', COUNT(*) FILTER (WHERE is_false_positive = true),
        'last_analysis', MAX(analyzed_at)
    )
    INTO analytics
    FROM analysis_results
    WHERE search_profile_id = profile_id_param;
    
    RETURN analytics;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to search listings with full-text search
CREATE OR REPLACE FUNCTION search_listings_fts(search_query TEXT, limit_param INT DEFAULT 20)
RETURNS TABLE(
    id BIGINT,
    url TEXT,
    title TEXT,
    description TEXT,
    price DECIMAL(10,2),
    location TEXT,
    marketplace TEXT,
    created_at TIMESTAMPTZ,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.id,
        l.url,
        l.title,
        l.description,
        l.price,
        l.location,
        l.marketplace,
        l.created_at,
        ts_rank(to_tsvector('english', l.title || ' ' || COALESCE(l.description, '')), plainto_tsquery('english', search_query)) AS rank
    FROM listings l
    WHERE to_tsvector('english', l.title || ' ' || COALESCE(l.description, '')) @@ plainto_tsquery('english', search_query)
    ORDER BY rank DESC, l.created_at DESC
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get recent activity
CREATE OR REPLACE FUNCTION get_recent_activity(hours_param INT DEFAULT 24, limit_param INT DEFAULT 50)
RETURNS TABLE(
    activity_type TEXT,
    activity_time TIMESTAMPTZ,
    profile_name TEXT,
    listing_title TEXT,
    match_score DECIMAL(3,1),
    marketplace TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN ar.match_score >= 8.0 THEN 'high_match'
            WHEN ar.match_score >= 6.0 THEN 'medium_match'
            ELSE 'low_match'
        END as activity_type,
        ar.analyzed_at as activity_time,
        sp.name as profile_name,
        l.title as listing_title,
        ar.match_score,
        l.marketplace
    FROM analysis_results ar
    JOIN search_profiles sp ON ar.search_profile_id = sp.id
    JOIN listings l ON ar.listing_id = l.id
    WHERE ar.analyzed_at >= NOW() - (hours_param || ' hours')::INTERVAL
    ORDER BY ar.analyzed_at DESC
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INT DEFAULT 90)
RETURNS JSON AS $$
DECLARE
    deleted_counts JSON;
    listings_deleted INT;
    analyses_deleted INT;
BEGIN
    -- Delete old listings and their analysis results (cascading)
    DELETE FROM listings 
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND status NOT IN ('match_found');  -- Keep matches
    
    GET DIAGNOSTICS listings_deleted = ROW_COUNT;
    
    -- Delete old analysis results for deleted listings  
    DELETE FROM analysis_results
    WHERE analyzed_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND match_score < 5.0;  -- Keep higher scoring analyses
    
    GET DIAGNOSTICS analyses_deleted = ROW_COUNT;
    
    SELECT json_build_object(
        'listings_deleted', listings_deleted,
        'analyses_deleted', analyses_deleted,
        'cleanup_date', NOW()
    ) INTO deleted_counts;
    
    RETURN deleted_counts;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
