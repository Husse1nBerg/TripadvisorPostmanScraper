# app/scrapers/tripadvisor_scraper.py

import logging
from datetime import date
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# --- KEY CHANGE: Import the new parser function ---
from .parser_utils import parse_tripadvisor_price

BASE_URL = "https://www.tripadvisor.ca/Hotel_Review-{geo_id}-{hotel_id}-Reviews.html"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TripadvisorScraper:
    async def scrape_price(
        self,
        geo_id: str,
        hotel_id: str,
        checkin_date: date,
        checkout_date: date,
        debug: bool = False
    ) -> Optional[str]:
        full_url = f"{BASE_URL.format(geo_id=geo_id, hotel_id=hotel_id)}?c_in={checkin_date.strftime('%Y-%m-%d')}&c_out={checkout_date.strftime('%Y-%m-%d')}"

        logger.info(f"Launching browser to scrape URL: {full_url}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )

                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                await page.goto(full_url, timeout=60000, wait_until="domcontentloaded")
                await page.wait_for_timeout(5000) # Wait for page to fully render

                html_content = await page.content()
                await browser.close()
                
                if debug:
                    with open("debug.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info("Saved final, JS-rendered HTML to debug.html")

                # --- KEY CHANGE: Call the parser utility to do the work ---
                price = parse_tripadvisor_price(html_content)

                if price:
                    logger.info(f"SUCCESS! Found and parsed price: {price}")
                    return price
                else:
                    logger.warning("Could not find price in the final HTML. The site structure may have changed.")
                    return None

        except PlaywrightTimeoutError:
            logger.error("Timeout Error: The page navigation or a required element took too long to load.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred with Playwright: {e}", exc_info=True)
            return None