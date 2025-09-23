
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime

# -------------------------------------------------------------
# models.py
# Supabase client setup and utility functions for hotel price data
# - Loads Supabase configuration from environment variables
# - Provides functions to insert and fetch hotel price records
# -------------------------------------------------------------
"""
Database models and session management for hotel price scraping.
Uses Supabase Python client and loads configuration from environment variables.
"""

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("Supabase credentials not found in environment variables")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_price(hotel_name: str, price: float, checkin_date: datetime.datetime = None, checkout_date: datetime.datetime = None) -> dict:
    """
    Inserts a hotel price record into the Supabase 'prices' table.
    Tries multiple schema variations to match whatever exists.
    """
    import logging

    # Try different schema variations
    schemas_to_try = [
        # Variation 1: Full schema with snake_case
        {
            "hotel_name": hotel_name,
            "price": price,
            "checkin_date": checkin_date.isoformat() if checkin_date else None,
            "checkout_date": checkout_date.isoformat() if checkout_date else None,
            "scraped_at": datetime.datetime.utcnow().isoformat()
        },
        # Variation 2: Without dates
        {
            "hotel_name": hotel_name,
            "price": price,
        },
        # Variation 3: Just price with timestamp
        {
            "price": price,
        },
        # Variation 4: camelCase
        {
            "hotelName": hotel_name,
            "price": price,
        },
    ]

    last_error = None
    for i, data in enumerate(schemas_to_try):
        try:
            logging.info(f"Trying schema variation {i+1}: {list(data.keys())}")
            response = supabase.table("prices").insert(data).execute()
            logging.info(f"SUCCESS with schema variation {i+1}")
            return response.data
        except Exception as e:
            last_error = e
            logging.warning(f"Schema variation {i+1} failed: {e}")
            continue

    # If all variations failed, raise the last error
    raise last_error

def fetch_prices(hotel_name: str = None) -> list:
    """
    Fetches hotel price records from the Supabase 'prices' table.
    """
    query = supabase.table("prices")
    if hotel_name:
        query = query.select("*").eq("hotel_name", hotel_name)
    else:
        query = query.select("*")
    response = query.execute()
    return response.data