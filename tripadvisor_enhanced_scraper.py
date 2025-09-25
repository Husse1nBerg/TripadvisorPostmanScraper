#!/usr/bin/env python3
"""
Enhanced TripAdvisor Hotel Price Scraper

Improved version with better price detection, screenshots for debugging,
and more comprehensive selectors.
"""

import re
import json
import time
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


class TripAdvisorEnhancedScraper:
    def __init__(self, headless=True, debug=True):
        """
        Initialize the enhanced scraper.
        
        Args:
            headless (bool): Run browser in headless mode
            debug (bool): Enable debug features like screenshots
        """
        self.headless = headless
        self.debug = debug
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with enhanced options."""
        try:
            print("Setting up enhanced Chrome WebDriver...")
            
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Enhanced options for better compatibility
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Disable notifications and popups
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-extensions")
            
            # Suppress Chrome internal errors
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-gcm")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Automatically download and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            print("Enhanced Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def take_screenshot(self, filename="debug_screenshot.png"):
        """Take a screenshot for debugging purposes."""
        if self.debug and self.driver:
            try:
                screenshot_path = os.path.join(os.getcwd(), filename)
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
                return screenshot_path
            except Exception as e:
                print(f"Could not take screenshot: {e}")
        return None
    
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
            time.sleep(5)
            
            # Take initial screenshot
            if self.debug:
                self.take_screenshot("01_initial_page.png")
            
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
    
    def wait_and_interact_with_page(self):
        """Wait for content to load and try to interact with the page."""
        try:
            print("Waiting for page content to load...")
            
            # Wait for basic page elements
            time.sleep(3)
            
            # Try to scroll down to trigger lazy loading
            print("Scrolling to trigger content loading...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            # Try to find and click on price-related elements
            price_triggers = [
                "button[data-testid='price-button']",
                ".price-button",
                "[class*='price'] button",
                "[class*='rate'] button",
                "button[class*='price']",
                "button[class*='rate']"
            ]
            
            for selector in price_triggers:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"Clicking price trigger: {selector}")
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(2)
                            break
                except Exception:
                    continue
            
            # Scroll to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Take screenshot after interactions
            if self.debug:
                self.take_screenshot("02_after_interactions.png")
            
            return True
            
        except Exception as e:
            print(f"Error during page interaction: {e}")
            return False
    
    def extract_comprehensive_data(self):
        """Extract comprehensive data using multiple strategies."""
        try:
            pricing_data = {
                "extracted_at": datetime.now().isoformat(),
                "url": self.driver.current_url,
                "prices": [],
                "hotel_info": {},
                "booking_providers": [],
                "all_text_content": [],
                "page_source_snippet": ""
            }
            
            # Get page title
            pricing_data["page_title"] = self.driver.title
            
            # Extract hotel name with more comprehensive selectors
            hotel_name_selectors = [
                "h1[data-testid='hotel-name']",
                "h1.hotel-name",
                ".hotel-name h1",
                "h1[class*='hotel']",
                "h1",
                "[data-testid='hotel-title']",
                ".hotel-title",
                ".property-name",
                "[class*='property-name']"
            ]
            
            for selector in hotel_name_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.text.strip():
                            pricing_data["hotel_info"]["name"] = element.text.strip()
                            print(f"Found hotel name: {element.text.strip()}")
                            break
                    if pricing_data["hotel_info"].get("name"):
                        break
                except Exception:
                    continue
            
            # Extract hotel rating
            rating_selectors = [
                "[data-testid='rating']",
                ".rating",
                "[class*='rating']",
                ".stars",
                "[class*='stars']",
                ".bubble-rating",
                "[class*='bubble-rating']"
            ]
            
            for selector in rating_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.text.strip():
                            pricing_data["hotel_info"]["rating"] = element.text.strip()
                            print(f"Found rating: {element.text.strip()}")
                            break
                    if pricing_data["hotel_info"].get("rating"):
                        break
                except Exception:
                    continue
            
            # Comprehensive price extraction
            price_selectors = [
                # Data test IDs
                "[data-testid='price']",
                "[data-testid='rate']",
                "[data-testid='amount']",
                "[data-testid='cost']",
                
                # Class-based selectors
                ".price",
                ".rate",
                ".rate-amount",
                ".price-amount",
                ".cost",
                ".amount",
                
                # Attribute-based selectors
                "[class*='price']",
                "[class*='rate']",
                "[class*='amount']",
                "[class*='cost']",
                
                # Specific TripAdvisor selectors
                ".prw_rup_prw_meta_hsx_responsive_listing",
                ".prw_rup_prw_meta_hsx_listing",
                ".listing-price",
                ".hotel-price",
                ".booking-price",
                ".provider-price",
                
                # Generic selectors
                "[class*='booking']",
                "[class*='provider']",
                "[class*='listing']"
            ]
            
            print("Searching for prices with comprehensive selectors...")
            for selector in price_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and any(char.isdigit() for char in text):
                            # Check if it looks like a price
                            if any(currency in text for currency in ['$', '€', '£', '¥', 'CAD', 'USD', 'EUR', 'GBP']):
                                price_clean = re.sub(r'[^\d.,$€£¥CADUSDEURGBP]', '', text)
                                if price_clean and len(price_clean) > 1:
                                    pricing_data["prices"].append({
                                        "text": text,
                                        "clean": price_clean,
                                        "selector": selector,
                                        "element_html": element.get_attribute('outerHTML')[:300] + "..."
                                    })
                                    print(f"Found price: {text} (selector: {selector})")
                except Exception:
                    continue
            
            # Look for any text containing price-like patterns
            print("Searching for price patterns in all text...")
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '$') or contains(text(), '€') or contains(text(), '£') or contains(text(), 'CAD') or contains(text(), 'USD')]")
            
            for element in all_elements:
                text = element.text.strip()
                if text and len(text) < 100:  # Avoid very long text blocks
                    # Check if it looks like a price
                    if re.search(r'\$[\d,]+|\€[\d,]+|\£[\d,]+|CAD\s*[\d,]+|USD\s*[\d,]+', text):
                        price_clean = re.sub(r'[^\d.,$€£¥CADUSDEURGBP]', '', text)
                        if price_clean and len(price_clean) > 1:
                            pricing_data["prices"].append({
                                "text": text,
                                "clean": price_clean,
                                "selector": "text_pattern_search",
                                "element_html": element.get_attribute('outerHTML')[:200] + "..."
                            })
                            print(f"Found price pattern: {text}")
            
            # Remove duplicates
            seen_prices = set()
            unique_prices = []
            for price in pricing_data["prices"]:
                if price["clean"] not in seen_prices:
                    seen_prices.add(price["clean"])
                    unique_prices.append(price)
            pricing_data["prices"] = unique_prices
            
            # Get a snippet of page source for debugging
            page_source = self.driver.page_source
            pricing_data["page_source_snippet"] = page_source[:1000] + "..." if len(page_source) > 1000 else page_source
            
            print(f"Extracted {len(pricing_data['prices'])} unique prices")
            print(f"Hotel: {pricing_data['hotel_info'].get('name', 'Unknown')}")
            print(f"Rating: {pricing_data['hotel_info'].get('rating', 'N/A')}")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error extracting data: {e}")
            return None
    
    def scrape_hotel_prices(self, url, check_in_date=None, check_out_date=None, adults=2, rooms=1):
        """Main method to scrape hotel prices with enhanced detection."""
        print(f"Starting enhanced price scraping for URL: {url}")
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
            
            # Wait and interact with page
            self.wait_and_interact_with_page()
            
            # Extract comprehensive data
            pricing_data = self.extract_comprehensive_data()
            
            if pricing_data:
                pricing_data["hotel_id"] = hotel_id
                pricing_data["scraping_method"] = "enhanced_selenium_automation"
                pricing_data["travel_params"] = {
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "adults": adults,
                    "rooms": rooms
                }
            
            print("=" * 60)
            print("Enhanced scraping completed!")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            return None
        
        finally:
            self.close_driver()


def main():
    """Main function to run the enhanced scraper."""
    print("TripAdvisor Enhanced Hotel Price Scraper")
    print("=" * 45)
    
    # Ask user for preferences
    headless_input = input("Run in headless mode? (y/n) [default: y]: ").strip().lower()
    headless = headless_input != 'n'
    
    debug_input = input("Enable debug mode (screenshots)? (y/n) [default: y]: ").strip().lower()
    debug = debug_input != 'n'
    
    scraper = TripAdvisorEnhancedScraper(headless=headless, debug=debug)
    
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
        output_file = f"tripadvisor_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pricing_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Display summary
        print(f"\nEnhanced Scraping Summary:")
        print(f"Page Title: {pricing_data.get('page_title', 'Unknown')}")
        print(f"Hotel: {pricing_data.get('hotel_info', {}).get('name', 'Unknown')}")
        print(f"Rating: {pricing_data.get('hotel_info', {}).get('rating', 'N/A')}")
        print(f"Prices found: {len(pricing_data.get('prices', []))}")
        
        if pricing_data.get('prices'):
            print("\nAll prices found:")
            for i, price in enumerate(pricing_data['prices']):
                print(f"  {i+1}. {price['text']} (clean: {price['clean']})")
        else:
            print("\nNo prices found. Check the screenshots and JSON file for debugging.")
            if debug:
                print("Screenshots saved for debugging purposes.")
    else:
        print("\nEnhanced scraping failed. Please check the URL and try again.")


if __name__ == "__main__":
    main()

