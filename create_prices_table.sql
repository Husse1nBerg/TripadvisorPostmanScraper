-- Create the prices table in Supabase
-- Run this SQL in your Supabase SQL Editor

-- Drop existing table if you want to start fresh (CAUTION: This deletes all data!)
-- DROP TABLE IF EXISTS prices;

-- Create prices table with proper schema
CREATE TABLE IF NOT EXISTS prices (
    id BIGSERIAL PRIMARY KEY,
    hotel_name TEXT,
    price DECIMAL NOT NULL,
    checkin_date TIMESTAMPTZ,
    checkout_date TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_prices_hotel_name ON prices(hotel_name);
CREATE INDEX IF NOT EXISTS idx_prices_scraped_at ON prices(scraped_at);

-- Enable Row Level Security (RLS) - optional but recommended
ALTER TABLE prices ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust based on your security needs)
CREATE POLICY "Enable all access for prices table" ON prices
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Verify table was created
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'prices'
ORDER BY ordinal_position;