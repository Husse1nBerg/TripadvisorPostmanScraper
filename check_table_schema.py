#!/usr/bin/env python3
"""
Check the actual schema of the Supabase prices table
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Attempting to fetch existing data from 'prices' table to see column names...")

try:
    # Try to select all columns with a limit
    response = supabase.table("prices").select("*").limit(1).execute()

    if response.data:
        print("\nSUCCESS: Table exists! Found columns:")
        for key in response.data[0].keys():
            print(f"  - {key}")
    else:
        print("\nSUCCESS: Table exists but is empty")
        print("Need to check table structure in Supabase dashboard")

except Exception as e:
    print(f"\nERROR: {e}")
    print("\nPlease check your Supabase dashboard to see the actual column names in the 'prices' table")

print("\n" + "="*50)
print("Common Supabase table schemas:")
print("="*50)
print("\nOption 1 (snake_case):")
print("  - id, hotel_name, price, checkin_date, checkout_date, scraped_at")
print("\nOption 2 (camelCase):")
print("  - id, hotelName, price, checkinDate, checkoutDate, scrapedAt")
print("\nOption 3 (minimal):")
print("  - id, price, created_at")
print("\nYou need to match the code to whatever schema you created in Supabase.")