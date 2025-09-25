#!/usr/bin/env python3
"""
TripAdvisor Hotel Price Scraper (Browser Automation)

Uses Selenium to bypass API restrictions and scrape prices directly from the rendered page.
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class TripAdvisorSeleniumScraper:
    def __init__(self, headless=True):
        """
        Initialize the scraper with Chrome WebDriver.
        
        Args:
            headless (bool): Run browser in headless mode (default: True)
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Additional options for better compatibility
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Disable images and CSS for faster loading (optional)
            # chrome_options.add_argument("--disable-images")
            # chrome_options.add_argument("--disable-css")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            print("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            print("Make sure ChromeDriver is installed and in your PATH")
            return False
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def parse_tripadvisor_url(self, url):
        """
        Parse TripAdvisor URL to extract hotel ID.
        
        Args:
            url (str): TripAdvisor hotel URL
            
        Returns:
            int or None: Hotel ID if found, None otherwise
        """
        try:
            # Extract hotel ID using regex pattern
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
        """
        Navigate to the TripAdvisor hotel page.
        
        Args:
            url (str): TripAdvisor hotel URL
            
        Returns:
            bool: True if successful, False otherwise
        """
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
    
    def set_travel_dates(self, check_in_date=None, check_out_date=None, adults=2, rooms=1):
        """
        Set travel parameters on the hotel page.
        
        Args:
            check_in_date (str): Check-in date in YYYY-MM-DD format
            check_out_date (str): Check-out date in YYYY-MM-DD format
            adults (int): Number of adults
            rooms (int): Number of rooms
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Default dates if not provided
            if not check_in_date:
                check_in_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            if not check_out_date:
                check_out_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            
            print(f"Setting travel parameters:")
            print(f"  Check-in: {check_in_date}")
            print(f"  Check-out: {check_out_date}")
            print(f"  Adults: {adults}")
            print(f"  Rooms: {rooms}")
            
            # Look for date picker or booking widget
            # TripAdvisor has different layouts, so we'll try multiple selectors
            
            # Try to find and click on date inputs
            date_selectors = [
                "input[data-testid='checkin-date']",
                "input[data-testid='checkout-date']",
                "input[name='checkin']",
                "input[name='checkout']",
                ".checkin-date input",
                ".checkout-date input"
            ]
            
            # For now, we'll just log the attempt and continue
            # In a real implementation, you'd interact with the date picker
            print("Note: Date setting would require interaction with TripAdvisor's date picker")
            print("This is complex due to dynamic JavaScript widgets")
            
            return True
            
        except Exception as e:
            print(f"Error setting travel dates: {e}")
            return False
    
    def extract_pricing_data(self):
        """
        Extract pricing information from the loaded page.
        
        Returns:
            dict: Extracted pricing data
        """
        try:
            pricing_data = {
                "extracted_at": datetime.now().isoformat(),
                "url": self.driver.current_url,
                "prices": [],
                "hotel_info": {},
                "raw_html_snippets": []
            }
            
            # Extract hotel name
            hotel_name_selectors = [
                "h1[data-testid='hotel-name']",
                "h1.hotel-name",
                ".hotel-name h1",
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
            
            # Extract prices - TripAdvisor has various price selectors
            price_selectors = [
                "[data-testid='price']",
                ".price",
                ".rate",
                ".rate-amount",
                ".price-amount",
                "[class*='price']",
                "[class*='rate']"
            ]
            
            for selector in price_selectors:
                try:
                    price_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in price_elements:
                        price_text = element.text.strip()
                        if price_text and any(char.isdigit() for char in price_text):
                            # Clean up price text
                            price_clean = re.sub(r'[^\d.,$€£¥]', '', price_text)
                            if price_clean:
                                pricing_data["prices"].append({
                                    "text": price_text,
                                    "clean": price_clean,
                                    "element_html": element.get_attribute('outerHTML')[:200] + "..."
                                })
                except Exception as e:
                    continue
            
            # Look for booking provider prices
            provider_selectors = [
                "[data-testid='booking-provider']",
                ".booking-provider",
                ".provider-price",
                "[class*='booking']"
            ]
            
            for selector in provider_selectors:
                try:
                    provider_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in provider_elements:
                        provider_text = element.text.strip()
                        if provider_text:
                            pricing_data["raw_html_snippets"].append({
                                "type": "booking_provider",
                                "text": provider_text,
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
            
            print(f"Extracted {len(pricing_data['prices'])} unique prices")
            print(f"Found hotel: {pricing_data['hotel_info'].get('name', 'Unknown')}")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error extracting pricing data: {e}")
            return None
    
    def scrape_hotel_prices(self, url, check_in_date=None, check_out_date=None, adults=2, rooms=1):
        """
        Main method to scrape hotel prices using browser automation.
        
        Args:
            url (str): TripAdvisor hotel URL
            check_in_date (str): Check-in date in YYYY-MM-DD format
            check_out_date (str): Check-out date in YYYY-MM-DD format
            adults (int): Number of adults
            rooms (int): Number of rooms
            
        Returns:
            dict: Pricing data or None if scraping fails
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
            
            # Set travel parameters (optional - may not work on all pages)
            self.set_travel_dates(check_in_date, check_out_date, adults, rooms)
            
            # Wait for page to fully load
            print("Waiting for page to load completely...")
            time.sleep(5)
            
            # Extract pricing data
            pricing_data = self.extract_pricing_data()
            
            if pricing_data:
                pricing_data["hotel_id"] = hotel_id
                pricing_data["scraping_method"] = "selenium_browser_automation"
            
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
    print("TripAdvisor Hotel Price Scraper (Browser Automation)")
    print("=" * 50)
    
    # Ask user for headless mode preference
    headless_input = input("Run in headless mode? (y/n) [default: y]: ").strip().lower()
    headless = headless_input != 'n'
    
    scraper = TripAdvisorSeleniumScraper(headless=headless)
    
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
        output_file = f"tripadvisor_prices_selenium_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pricing_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Display summary
        print(f"\nScraping Summary:")
        print(f"Hotel: {pricing_data.get('hotel_info', {}).get('name', 'Unknown')}")
        print(f"Prices found: {len(pricing_data.get('prices', []))}")
        if pricing_data.get('prices'):
            print("Sample prices:")
            for i, price in enumerate(pricing_data['prices'][:3]):
                print(f"  {i+1}. {price['text']}")
    else:
        print("\nScraping failed. Please check the URL and try again.")


if __name__ == "__main__":
    main()
