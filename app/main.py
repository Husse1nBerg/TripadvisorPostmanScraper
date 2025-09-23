# app/main.py

import logging
import re
import sys
import asyncio  # <-- Required for the fix
from datetime import date, datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, validator

from app.database.models import fetch_prices, insert_price
from app.scrapers.tripadvisor_scraper import TripadvisorScraper

# --- THIS IS THE CRITICAL FIX for NotImplementedError on Windows ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# -------------------------------------------------------------------

# --- App and Scraper Setup ---
app = FastAPI(
    title="Tripadvisor Price Scraper API",
    description="An API to scrape hotel prices from Tripadvisor and store them in Supabase.",
)
scraper = TripadvisorScraper()

# --- Logging and Rate Limiting ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper_api")
rate_limit = {}
RATE_LIMIT_SECONDS = 2

# --- Pydantic Models ---
class ScrapeRequest(BaseModel):
    geo_id: str = Field(..., example="g155032")
    hotel_id: str = Field(..., example="d14134983")
    checkin_date: date
    checkout_date: date

    @validator("geo_id")
    def geo_id_format(cls, v):
        if not re.match(r"^g\d+$", v):
            raise ValueError("Invalid geo_id format. Must be 'g' followed by digits.")
        return v

    @validator("hotel_id")
    def hotel_id_format(cls, v):
        if not re.match(r"^d\d+$", v):
            raise ValueError("Invalid hotel_id format. Must be 'd' followed by digits.")
        return v

    @validator("checkout_date")
    def checkin_before_checkout(cls, v, values):
        if "checkin_date" in values and v <= values["checkin_date"]:
            raise ValueError("Checkout date must be after check-in date.")
        return v

class ScrapeResponse(BaseModel):
    hotel_id: str
    checkin_date: date
    checkout_date: date
    price: Optional[str]
    status: str
    
class PriceResponse(BaseModel):
    hotel_name: str
    price: float
    checkin_date: Optional[date]
    checkout_date: Optional[date]
    scraped_at: datetime

# --- API Endpoints ---
@app.post("/scrape-price/", response_model=ScrapeResponse)
async def scrape_and_store_price(request: ScrapeRequest, req: Request):
    client_ip = req.client.host
    now = datetime.now()
    if client_ip in rate_limit and (now - rate_limit[client_ip]).total_seconds() < RATE_LIMIT_SECONDS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    rate_limit[client_ip] = now

    price = await scraper.scrape_price(
        geo_id=request.geo_id,
        hotel_id=request.hotel_id,
        checkin_date=request.checkin_date,
        checkout_date=request.checkout_date,
        debug=True
    )

    if not price:
        return ScrapeResponse(hotel_id=request.hotel_id, checkin_date=request.checkin_date, checkout_date=request.checkout_date, price=None, status="Failed to find price")

    try:
        price_float = float(price)
        await run_in_threadpool(
            insert_price,
            hotel_name=request.hotel_id,
            price=price_float,
            checkin_date=request.checkin_date,
            checkout_date=request.checkout_date,
        )
        return ScrapeResponse(hotel_id=request.hotel_id, checkin_date=request.checkin_date, checkout_date=request.checkout_date, price=price, status="Success")
    except Exception as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {db_err}")

@app.get("/prices/{hotel_id}", response_model=List[PriceResponse])
async def get_prices_for_hotel(hotel_id: str):
    try:
        results = await run_in_threadpool(fetch_prices, hotel_name=hotel_id)
        return results
    except Exception as db_err:
        raise HTTPException(status_code=500, detail=f"Database error while fetching: {db_err}")