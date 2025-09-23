
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
    """
    data = {
        "hotel_name": hotel_name,
        "price": price,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "scraped_at": datetime.datetime.utcnow()
    }
    response = supabase.table("prices").insert(data).execute()
    return response.data

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