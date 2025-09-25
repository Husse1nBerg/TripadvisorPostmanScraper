import logging
import re
import sys
import asyncio
from datetime import date, datetime
from typing import List, Optional
import os

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

# --- Database and Scraper Imports ---
try:
    from app.database.models import fetch_prices, insert_price
    from app.scrapers.tripadvisor_scraper import TripadvisorScraper
except ImportError as e:
    logging.error(f"Error importing modules: {e}")
    raise RuntimeError("Could not import necessary modules. Please check your project structure.") from e

# --- Environment Variable Loading ---
from dotenv import load_dotenv
load_dotenv()

# --- Windows asyncio fix ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- App Setup ---
app = FastAPI(
    title="Tripadvisor Price Scraper API",
    description="An API to scrape hotel prices from Tripadvisor and store them in a Supabase database.",
    version="1.0.0",
)

# --- Pydantic Models for API Requests ---
class ScrapeRequest(BaseModel):
    geo_id: str = Field(..., description="Geo ID for the location (e.g., 'g155032' for Montreal)")
    hotel_id: str = Field(..., description="Hotel ID on Tripadvisor (e.g., 'd14134983')")
    checkin_date: date
    checkout_date: date

# --- API Endpoints ---
@app.post("/scrape-price/")
async def scrape_price_endpoint(request: ScrapeRequest):
    """
    Scrapes the price from Tripadvisor based on the provided details and stores it.
    """
    logging.info(f"Received scraping request for hotel_id: {request.hotel_id}")

    # Validate inputs to prevent "string" literals
    if request.hotel_id == "string" or request.geo_id == "string":
        raise HTTPException(
            status_code=400,
            detail="Invalid hotel_id or geo_id. Please provide actual values, not 'string'."
        )

    # Basic validation for TripAdvisor IDs
    if not request.hotel_id.startswith('d') or not request.geo_id.startswith('g'):
        raise HTTPException(
            status_code=400,
            detail="Invalid ID format. hotel_id should start with 'd' and geo_id should start with 'g'."
        )

    try:
        scraper = TripadvisorScraper()
        # *** THIS IS THE CORRECTED LINE ***
        price = await scraper.scrape_price(
            geo_id=request.geo_id,
            hotel_id=request.hotel_id,
            checkin_date=request.checkin_date,
            checkout_date=request.checkout_date
        )

        if price is None:
            logging.warning("Price could not be scraped.")
            raise HTTPException(status_code=404, detail="Price not found on the page.")

        logging.info(f"Successfully scraped price: {price}")

        # --- Database Insertion with Error Handling ---
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            if not supabase_url:
                logging.error("FATAL: SUPABASE_URL environment variable not found.")
                raise HTTPException(status_code=500, detail="Server configuration error: SUPABASE_URL is not set.")

            logging.info("Attempting to insert price into the database.")
            hotel_name = f"{request.hotel_id}"

            # Convert date objects to datetime objects for Supabase
            checkin_datetime = datetime.combine(request.checkin_date, datetime.min.time())
            checkout_datetime = datetime.combine(request.checkout_date, datetime.min.time())

            db_response = await run_in_threadpool(
                insert_price,
                hotel_name=hotel_name,
                price=float(price),
                checkin_date=checkin_datetime,
                checkout_date=checkout_datetime
            )
            logging.info(f"Database insertion response: {db_response}")

            return {"hotel_name": hotel_name, "price": price, "status": "success"}

        except Exception as e:
            logging.error(f"DATABASE ERROR: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An internal error occurred while saving the price: {e}")

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"SCRAPING ERROR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during scraping: {e}")

@app.get("/prices/{hotel_name}")
async def get_prices(hotel_name: str):
    """
    Retrieves all stored prices for a specific hotel.
    """
    logging.info(f"Fetching prices for hotel: {hotel_name}")
    try:
        # Using run_in_threadpool here is correct because fetch_prices is a synchronous function
        prices = await run_in_threadpool(fetch_prices, hotel_name=hotel_name)
        if not prices:
            logging.warning(f"No prices found for hotel: {hotel_name}")
            raise HTTPException(status_code=404, detail="No prices found for this hotel.")
        return prices
    except Exception as e:
        logging.error(f"An error occurred while fetching prices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")