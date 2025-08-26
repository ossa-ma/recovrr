-- Create search_profiles table
CREATE TABLE IF NOT EXISTS search_profiles (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    
    -- Item details
    make TEXT,
    model TEXT,
    color TEXT,
    size TEXT,
    description TEXT,
    unique_features TEXT,
    
    -- Search parameters
    location TEXT,
    price_min DECIMAL(10,2),
    price_max DECIMAL(10,2),
    search_terms JSONB DEFAULT '[]',
    
    -- Contact information
    owner_email TEXT NOT NULL,
    owner_phone TEXT,
    
    -- Status and metadata
    active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create listings table
CREATE TABLE IF NOT EXISTS listings (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    
    -- Listing details
    title TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    location TEXT,
    image_urls JSONB DEFAULT '[]',
    
    -- Marketplace info
    marketplace TEXT NOT NULL,
    external_id TEXT,
    
    -- Status tracking
    status TEXT DEFAULT 'new' NOT NULL CHECK (status IN ('new', 'analyzed', 'match_found', 'ignored')),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create analysis_results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign keys
    listing_id BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    search_profile_id BIGINT NOT NULL REFERENCES search_profiles(id) ON DELETE CASCADE,
    
    -- Analysis results
    match_score DECIMAL(3,1) NOT NULL CHECK (match_score >= 0 AND match_score <= 10),
    reasoning TEXT,
    confidence_level TEXT NOT NULL CHECK (confidence_level IN ('low', 'medium', 'high')),
    key_indicators JSONB DEFAULT '[]',
    concerns JSONB DEFAULT '[]',
    recommendation TEXT NOT NULL CHECK (recommendation IN ('investigate', 'ignore', 'high_priority')),
    
    -- AI model info
    model_used TEXT,
    analysis_version TEXT,
    
    -- Status and actions
    notification_sent BOOLEAN DEFAULT FALSE NOT NULL,
    reviewed_by_human BOOLEAN DEFAULT FALSE NOT NULL,
    is_false_positive BOOLEAN,
    
    -- Timestamps
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    notification_sent_at TIMESTAMPTZ
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_search_profiles_active ON search_profiles(active);
CREATE INDEX IF NOT EXISTS idx_search_profiles_owner_email ON search_profiles(owner_email);

CREATE INDEX IF NOT EXISTS idx_listings_url ON listings(url);
CREATE INDEX IF NOT EXISTS idx_listings_marketplace ON listings(marketplace);
CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
CREATE INDEX IF NOT EXISTS idx_listings_created_at ON listings(created_at);

CREATE INDEX IF NOT EXISTS idx_analysis_results_listing_id ON analysis_results(listing_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_search_profile_id ON analysis_results(search_profile_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_match_score ON analysis_results(match_score);
CREATE INDEX IF NOT EXISTS idx_analysis_results_notification_sent ON analysis_results(notification_sent);

-- Create full-text search index for listings
CREATE INDEX IF NOT EXISTS idx_listings_title_fts ON listings USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_listings_description_fts ON listings USING gin(to_tsvector('english', description));

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for search_profiles updated_at
DROP TRIGGER IF EXISTS update_search_profiles_updated_at ON search_profiles;
CREATE TRIGGER update_search_profiles_updated_at
    BEFORE UPDATE ON search_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
