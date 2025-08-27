-- Create a function to get current user's email (in public schema)
CREATE OR REPLACE FUNCTION public.get_user_email() 
RETURNS TEXT AS $$
    SELECT COALESCE(
        current_setting('request.jwt.claims', true)::json->>'email',
        (current_setting('request.jwt.claims', true)::json->'user_metadata'->>'email')
    )::text;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Create a function to get current user's role (in public schema)
CREATE OR REPLACE FUNCTION public.get_user_role() 
RETURNS TEXT AS $$
    SELECT COALESCE(
        current_setting('request.jwt.claims', true)::json->>'role',
        'anon'
    )::text;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Enable Row Level Security (RLS) for all tables
ALTER TABLE search_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;

-- Policy for search_profiles: Users can only access their own profiles
CREATE POLICY "Users can view own search profiles" ON search_profiles
    FOR SELECT TO authenticated
    USING (public.get_user_email() = owner_email);

CREATE POLICY "Users can insert own search profiles" ON search_profiles
    FOR INSERT TO authenticated
    WITH CHECK (public.get_user_email() = owner_email);

CREATE POLICY "Users can update own search profiles" ON search_profiles
    FOR UPDATE TO authenticated
    USING (public.get_user_email() = owner_email)
    WITH CHECK (public.get_user_email() = owner_email);

CREATE POLICY "Users can delete own search profiles" ON search_profiles
    FOR DELETE TO authenticated
    USING (public.get_user_email() = owner_email);

-- Service role can access all data (for backend operations)
CREATE POLICY "Service role full access search_profiles" ON search_profiles
    FOR ALL TO service_role
    USING (public.get_user_role() = 'service_role');

-- Policy for listings: Anyone can read (for analysis), service role can modify
CREATE POLICY "Anyone can view listings" ON listings
    FOR SELECT
    USING (true);

CREATE POLICY "Service role can manage listings" ON listings
    FOR ALL TO service_role
    USING (public.get_user_role() = 'service_role');

-- Policy for analysis_results: Users can view results for their profiles
CREATE POLICY "Users can view analysis results for their profiles" ON analysis_results
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM search_profiles 
            WHERE id = analysis_results.search_profile_id 
            AND owner_email = public.get_user_email()
        )
    );

CREATE POLICY "Service role can manage analysis results" ON analysis_results
    FOR ALL TO service_role
    USING (public.get_user_role() = 'service_role');