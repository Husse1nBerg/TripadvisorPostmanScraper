#!/usr/bin/env python3
"""
TripAdvisor Hotel Price Scraper (Auto WebDriver Management)

Enhanced version with automatic ChromeDriver management using webdriver-manager.
"""

import re
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


class TripAdvisorAutoScraper:
    def __init__(self, headless=True):
        """
        Initialize the scraper with automatic ChromeDriver management.
        
        Args:
            headless (bool): Run browser in headless mode (default: True)
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with automatic driver management."""
        try:
            print("Setting up Chrome WebDriver with automatic driver management...")
            
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Additional options for better compatibility
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Disable notifications and popups
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-extensions")
            
            # Suppress Chrome internal errors and logging
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-gcm")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--log-level=3")  # Only show fatal errors
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Automatically download and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            print("Chrome WebDriver initialized successfully with auto-managed driver")
            return True
            
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            print("Make sure Chrome browser is installed")
            return False
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def parse_tripadvisor_url(self, url):
        """Parse TripAdvisor URL to extract hotel ID."""
        try:
            hotel_id_match = re.search(r'-d(\d+)', url)
            if not hotel_id_match:
                print(f"Error: Could not extract hotel ID from URL: {url}")
                return None
            
            hotel_id = int(hotel_id_match.group(1))
            print(f"Successfully parsed URL - Hotel ID: {hotel_id}")
            return hotel_id
            
        except Exception as e:
            print(f"Error parsing URL: {e}")
            return None
    
    def navigate_to_hotel_page(self, url):
        """Navigate to the TripAdvisor hotel page."""
        try:
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we're on the right page
            if "tripadvisor" in self.driver.current_url.lower():
                print("Successfully loaded TripAdvisor page")
                return True
            else:
                print(f"Unexpected redirect to: {self.driver.current_url}")
                return False
                
        except Exception as e:
            print(f"Error navigating to page: {e}")
            return False
    
    def wait_for_prices_to_load(self):
        """Wait for price elements to load on the page."""
        try:
            print("Waiting for prices to load...")
            
            # Wait for any price-related elements to appear
            price_selectors = [
                "[data-testid='price']",
                ".price",
                ".rate",
                "[class*='price']",
                "[class*='rate']"
            ]
            
            for selector in price_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"Found price elements with selector: {selector}")
                    return True
                except TimeoutException:
                    continue
            
            # If no specific price elements found, wait a bit more for general content
            time.sleep(5)
            print("No specific price elements found, continuing with general content")
            return True
            
        except Exception as e:
            print(f"Error waiting for prices: {e}")
            return False
    
    def extract_pricing_data(self):
        """Extract comprehensive pricing information from the loaded page."""
        try:
            pricing_data = {
                "extracted_at": datetime.now().isoformat(),
                "url": self.driver.current_url,
                "prices": [],
                "hotel_info": {},
                "booking_providers": [],
                "raw_html_snippets": []
            }
            
            # Extract hotel name
            hotel_name_selectors = [
                "h1[data-testid='hotel-name']",
                "h1.hotel-name",
                ".hotel-name h1",
                "h1[class*='hotel']",
                "h1"
            ]
            
            for selector in hotel_name_selectors:
                try:
                    hotel_name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if hotel_name_element and hotel_name_element.text.strip():
                        pricing_data["hotel_info"]["name"] = hotel_name_element.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract hotel rating
            rating_selectors = [
                "[data-testid='rating']",
                ".rating",
                "[class*='rating']",
                ".stars"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if rating_element and rating_element.text.strip():
                        pricing_data["hotel_info"]["rating"] = rating_element.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract prices with multiple strategies
            price_selectors = [
                "[data-testid='price']",
                ".price",
                ".rate",
                ".rate-amount",
                ".price-amount",
                "[class*='price']",
                "[class*='rate']",
                "[class*='amount']"
            ]
            
            for selector in price_selectors:
                try:
                    price_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in price_elements:
                        price_text = element.text.strip()
                        if price_text and any(char.isdigit() for char in price_text):
                            # Clean up price text
                            price_clean = re.sub(r'[^\d.,$€£¥]', '', price_text)
                            if price_clean and len(price_clean) > 1:
                                pricing_data["prices"].append({
                                    "text": price_text,
                                    "clean": price_clean,
                                    "selector": selector,
                                    "element_html": element.get_attribute('outerHTML')[:200] + "..."
                                })
                except Exception as e:
                    continue
            
            # Look for booking provider information
            provider_selectors = [
                "[data-testid='booking-provider']",
                ".booking-provider",
                ".provider-price",
                "[class*='booking']",
                "[class*='provider']"
            ]
            
            for selector in provider_selectors:
                try:
                    provider_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in provider_elements:
                        provider_text = element.text.strip()
                        if provider_text:
                            pricing_data["booking_providers"].append({
                                "text": provider_text,
                                "selector": selector,
                                "html": element.get_attribute('outerHTML')[:300] + "..."
                            })
                except Exception as e:
                    continue
            
            # Remove duplicates from prices
            seen_prices = set()
            unique_prices = []
            for price in pricing_data["prices"]:
                if price["clean"] not in seen_prices:
                    seen_prices.add(price["clean"])
                    unique_prices.append(price)
            pricing_data["prices"] = unique_prices
            
            # Remove duplicates from providers
            seen_providers = set()
            unique_providers = []
            for provider in pricing_data["booking_providers"]:
                if provider["text"] not in seen_providers:
                    seen_providers.add(provider["text"])
                    unique_providers.append(provider)
            pricing_data["booking_providers"] = unique_providers
            
            print(f"Extracted {len(pricing_data['prices'])} unique prices")
            print(f"Found {len(pricing_data['booking_providers'])} booking providers")
            print(f"Hotel: {pricing_data['hotel_info'].get('name', 'Unknown')}")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error extracting pricing data: {e}")
            return None
    
    def scrape_hotel_prices(self, url, check_in_date=None, check_out_date=None, adults=2, rooms=1):
        """
        Main method to scrape hotel prices using browser automation.
        """
        print(f"Starting browser-based price scraping for URL: {url}")
        print("=" * 60)
        
        # Setup WebDriver
        if not self.setup_driver():
            return None
        
        try:
            # Parse URL to get hotel ID
            hotel_id = self.parse_tripadvisor_url(url)
            if not hotel_id:
                return None
            
            # Navigate to hotel page
            if not self.navigate_to_hotel_page(url):
                return None
            
            # Wait for prices to load
            self.wait_for_prices_to_load()
            
            # Extract pricing data
            pricing_data = self.extract_pricing_data()
            
            if pricing_data:
                pricing_data["hotel_id"] = hotel_id
                pricing_data["scraping_method"] = "selenium_browser_automation_auto"
                pricing_data["travel_params"] = {
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "adults": adults,
                    "rooms": rooms
                }
            
            print("=" * 60)
            print("Scraping completed!")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            return None
        
        finally:
            self.close_driver()


def main():
    """Main function to run the scraper."""
    print("TripAdvisor Hotel Price Scraper (Auto WebDriver Management)")
    print("=" * 55)
    
    # Ask user for headless mode preference
    headless_input = input("Run in headless mode? (y/n) [default: y]: ").strip().lower()
    headless = headless_input != 'n'
    
    scraper = TripAdvisorAutoScraper(headless=headless)
    
    # Get URL from user
    url = input("Enter TripAdvisor hotel URL: ").strip()
    if not url:
        print("Error: No URL provided")
        return
    
    # Optional travel parameters
    print("\nOptional travel parameters (press Enter for defaults):")
    check_in = input("Check-in date (YYYY-MM-DD) [default: tomorrow]: ").strip() or None
    check_out = input("Check-out date (YYYY-MM-DD) [default: day after tomorrow]: ").strip() or None
    adults_input = input("Number of adults [default: 2]: ").strip()
    adults = int(adults_input) if adults_input.isdigit() else 2
    rooms_input = input("Number of rooms [default: 1]: ").strip()
    rooms = int(rooms_input) if rooms_input.isdigit() else 1
    
    # Scrape prices
    pricing_data = scraper.scrape_hotel_prices(url, check_in, check_out, adults, rooms)
    
    if pricing_data:
        # Save results to file
        output_file = f"tripadvisor_prices_auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pricing_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Display summary
        print(f"\nScraping Summary:")
        print(f"Hotel: {pricing_data.get('hotel_info', {}).get('name', 'Unknown')}")
        print(f"Rating: {pricing_data.get('hotel_info', {}).get('rating', 'N/A')}")
        print(f"Prices found: {len(pricing_data.get('prices', []))}")
        print(f"Booking providers: {len(pricing_data.get('booking_providers', []))}")
        
        if pricing_data.get('prices'):
            print("\nSample prices:")
            for i, price in enumerate(pricing_data['prices'][:5]):
                print(f"  {i+1}. {price['text']} (clean: {price['clean']})")
        
        if pricing_data.get('booking_providers'):
            print("\nBooking providers found:")
            for i, provider in enumerate(pricing_data['booking_providers'][:3]):
                print(f"  {i+1}. {provider['text'][:100]}...")
    else:
        print("\nScraping failed. Please check the URL and try again.")


if __name__ == "__main__":
    main()
