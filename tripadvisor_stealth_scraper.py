#!/usr/bin/env python3
"""
TripAdvisor Stealth Scraper

This version uses advanced techniques to bypass TripAdvisor's bot detection:
- Undetected Chrome driver
- Human-like behavior simulation
- Stealth browser configuration
- Random delays and interactions
"""

import re
import json
import time
import random
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


class TripAdvisorStealthScraper:
    def __init__(self, headless=False):  # Default to visible for better stealth
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_stealth_driver(self):
        """Setup Chrome WebDriver with stealth configuration."""
        try:
            print("Setting up stealth Chrome WebDriver...")
            
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless=new")  # Use new headless mode
            
            # Stealth configuration to avoid detection
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Window and display settings
            chrome_options.add_argument("--window-size=1366,768")
            chrome_options.add_argument("--start-maximized")
            
            # User agent and language
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
            
            # Disable automation indicators
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Faster loading
            chrome_options.add_argument("--disable-javascript")  # This might help avoid detection
            
            # Network and performance
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            
            # Disable notifications and popups
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            
            # Automatically download and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Execute stealth scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            print("Stealth Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error setting up stealth WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def human_like_delay(self, min_seconds=1, max_seconds=3):
        """Add human-like random delays."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def human_like_scroll(self):
        """Simulate human-like scrolling behavior."""
        try:
            # Random scroll patterns
            scroll_actions = [
                lambda: self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);"),
                lambda: self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);"),
                lambda: self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight*3/4);"),
                lambda: self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"),
                lambda: self.driver.execute_script("window.scrollTo(0, 0);")
            ]
            
            # Perform 2-4 random scrolls
            num_scrolls = random.randint(2, 4)
            for _ in range(num_scrolls):
                action = random.choice(scroll_actions)
                action()
                self.human_like_delay(1, 2)
                
        except Exception as e:
            print(f"Error during human-like scrolling: {e}")
    
    def simulate_human_behavior(self):
        """Simulate human-like behavior on the page."""
        try:
            print("Simulating human-like behavior...")
            
            # Random mouse movements (if not headless)
            if not self.headless:
                try:
                    actions = ActionChains(self.driver)
                    # Move mouse to random positions
                    for _ in range(random.randint(2, 5)):
                        x = random.randint(100, 800)
                        y = random.randint(100, 600)
                        actions.move_by_offset(x, y)
                        actions.perform()
                        self.human_like_delay(0.5, 1.5)
                except Exception:
                    pass
            
            # Human-like scrolling
            self.human_like_scroll()
            
            # Random page interactions
            try:
                # Try to find and hover over elements
                elements = self.driver.find_elements(By.TAG_NAME, "div")
                if elements:
                    random_element = random.choice(elements[:10])  # Pick from first 10
                    if random_element.is_displayed():
                        actions = ActionChains(self.driver)
                        actions.move_to_element(random_element).perform()
                        self.human_like_delay(1, 2)
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            print(f"Error simulating human behavior: {e}")
            return False
    
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
    
    def navigate_with_stealth(self, url):
        """Navigate to the page with stealth techniques."""
        try:
            print(f"Navigating to: {url}")
            
            # First, go to Google to establish a "normal" browsing pattern
            print("Establishing normal browsing pattern...")
            self.driver.get("https://www.google.com")
            self.human_like_delay(2, 4)
            
            # Then navigate to TripAdvisor
            self.driver.get(url)
            self.human_like_delay(3, 5)
            
            # Check if we're blocked
            page_source = self.driver.page_source.lower()
            if any(blocked_word in page_source for blocked_word in [
                "unusual activity", "bot activity", "automated", "blocked", 
                "access denied", "forbidden", "captcha", "robot"
            ]):
                print("❌ Still detected as bot. Trying alternative approach...")
                return False
            
            print("✅ Successfully loaded page without detection")
            return True
            
        except Exception as e:
            print(f"Error during stealth navigation: {e}")
            return False
    
    def extract_prices_stealth(self):
        """Extract prices using stealth techniques."""
        try:
            print("Extracting prices with stealth approach...")
            
            pricing_data = {
                "extracted_at": datetime.now().isoformat(),
                "url": self.driver.current_url,
                "prices": [],
                "hotel_info": {},
                "scraping_method": "stealth_selenium"
            }
            
            # Get page title
            pricing_data["page_title"] = self.driver.title
            
            # Extract hotel name
            hotel_name_selectors = [
                "h1", "h2", ".hotel-name", "[data-testid*='hotel']", 
                "[class*='hotel']", "[class*='property']"
            ]
            
            for selector in hotel_name_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) < 100 and "hotel" in text.lower():
                            pricing_data["hotel_info"]["name"] = text
                            print(f"Found hotel name: {text}")
                            break
                    if pricing_data["hotel_info"].get("name"):
                        break
                except Exception:
                    continue
            
            # Look for prices in a more aggressive way
            print("Searching for prices...")
            
            # Get all text content and look for price patterns
            all_text = self.driver.find_elements(By.XPATH, "//*[text()]")
            price_patterns = [
                r'\$[\d,]+(?:\.\d{2})?',
                r'CAD\s*[\d,]+(?:\.\d{2})?',
                r'USD\s*[\d,]+(?:\.\d{2})?',
                r'€[\d,]+(?:\.\d{2})?',
                r'£[\d,]+(?:\.\d{2})?'
            ]
            
            for element in all_text:
                text = element.text.strip()
                if text and len(text) < 200:
                    for pattern in price_patterns:
                        if re.search(pattern, text):
                            pricing_data["prices"].append({
                                "text": text,
                                "pattern": pattern,
                                "element_tag": element.tag_name
                            })
                            print(f"Found price: {text}")
            
            # Remove duplicates
            seen_prices = set()
            unique_prices = []
            for price in pricing_data["prices"]:
                if price["text"] not in seen_prices:
                    seen_prices.add(price["text"])
                    unique_prices.append(price)
            pricing_data["prices"] = unique_prices
            
            print(f"Extracted {len(pricing_data['prices'])} unique prices")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error extracting prices: {e}")
            return None
    
    def scrape_hotel_prices_stealth(self, url):
        """Main stealth scraping method."""
        print(f"Starting stealth price scraping for URL: {url}")
        print("=" * 60)
        
        # Setup stealth WebDriver
        if not self.setup_stealth_driver():
            return None
        
        try:
            # Parse URL to get hotel ID
            hotel_id = self.parse_tripadvisor_url(url)
            if not hotel_id:
                return None
            
            # Navigate with stealth
            if not self.navigate_with_stealth(url):
                print("❌ Stealth navigation failed - still being detected")
                return None
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Extract prices
            pricing_data = self.extract_prices_stealth()
            
            if pricing_data:
                pricing_data["hotel_id"] = hotel_id
            
            print("=" * 60)
            print("Stealth scraping completed!")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error during stealth scraping: {e}")
            return None
        
        finally:
            self.close_driver()


def main():
    """Main function to run the stealth scraper."""
    print("TripAdvisor Stealth Scraper")
    print("=" * 35)
    print("This version uses advanced techniques to bypass bot detection.")
    print("=" * 35)
    
    # Ask user for preferences
    headless_input = input("Run in headless mode? (y/n) [default: n for better stealth]: ").strip().lower()
    headless = headless_input == 'y'
    
    scraper = TripAdvisorStealthScraper(headless=headless)
    
    # Get URL from user
    url = input("Enter TripAdvisor hotel URL: ").strip()
    if not url:
        print("Error: No URL provided")
        return
    
    # Scrape prices
    pricing_data = scraper.scrape_hotel_prices_stealth(url)
    
    if pricing_data:
        # Save results to file
        output_file = f"tripadvisor_stealth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pricing_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Display summary
        print(f"\nStealth Scraping Summary:")
        print(f"Page Title: {pricing_data.get('page_title', 'Unknown')}")
        print(f"Hotel: {pricing_data.get('hotel_info', {}).get('name', 'Unknown')}")
        print(f"Prices found: {len(pricing_data.get('prices', []))}")
        
        if pricing_data.get('prices'):
            print("\nPrices found:")
            for i, price in enumerate(pricing_data['prices']):
                print(f"  {i+1}. {price['text']}")
        else:
            print("\nNo prices found. TripAdvisor might have additional protection.")
    else:
        print("\nStealth scraping failed. TripAdvisor's bot detection is very advanced.")


if __name__ == "__main__":
    main()

