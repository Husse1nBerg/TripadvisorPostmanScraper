# app/scrapers/tripadvisor_scraper.py

import logging
import os
from datetime import date
from typing import Optional
from dotenv import load_dotenv
import httpx

from .parser_utils import parse_tripadvisor_price

# Load environment variables
load_dotenv()
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
if not ZENROWS_API_KEY:
    raise EnvironmentError("ZENROWS_API_KEY not found in environment variables")

BASE_URL = "https://www.tripadvisor.ca/Hotel_Review-{geo_id}-{hotel_id}-Reviews.html"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- THE CLASS NAME IS NOW CORRECTED ---
class TripadvisorScraper:
    async def scrape_price(
        self,
        geo_id: str,
        hotel_id: str,
        checkin_date: date,
        checkout_date: date,
        debug: bool = False
    ) -> Optional[str]:
        target_url = f"{BASE_URL.format(geo_id=geo_id, hotel_id=hotel_id)}?c_in={checkin_date.strftime('%Y-%m-%d')}&c_out={checkout_date.strftime('%Y-%m-%d')}"

        logger.info(f"Requesting fully rendered page from ZenRows API: {target_url}")

        zenrows_api_url = "https://api.zenrows.com/v1/"
        params = {
            "url": target_url,
            "apikey": ZENROWS_API_KEY,
            "js_render": "true",
            "premium_proxy": "true",
            "wait_for": "h1", # Wait for the main title to ensure the page is loaded
            "wait": "10000",  # Increased wait time to 10 seconds
            "session_id": "1",  # Use session to maintain state
            "custom_headers": "true"  # Enable custom headers for better success rate
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(zenrows_api_url, params=params, timeout=180.0)
                response.raise_for_status()

                html_content = response.text

                if debug:
                    with open("debug.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info("Saved final HTML from API to debug.html")

                # Log some basic info about the HTML content
                logger.info(f"Received HTML content length: {len(html_content)} characters")

                # Check if we got a valid TripAdvisor page
                if "tripadvisor" not in html_content.lower():
                    logger.warning("Response does not appear to be from TripAdvisor")

                if "blocked" in html_content.lower() or "captcha" in html_content.lower():
                    logger.warning("Response may be blocked or contains captcha")

                price = parse_tripadvisor_price(html_content)

                if price:
                    logger.info(f"SUCCESS! Found and parsed price: {price}")
                    return price
                else:
                    logger.warning("Could not find price in the HTML. The site's layout may have changed.")
                    # Save the HTML for debugging if no price found
                    with open("debug_no_price.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info("Saved HTML content to debug_no_price.html for analysis")
                    return None

        except httpx.TimeoutException:
            logger.error("Timeout Error: The API request to ZenRows timed out.")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: ZenRows API returned status {e.response.status_code}. Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return None