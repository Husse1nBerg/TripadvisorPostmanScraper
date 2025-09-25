#!/usr/bin/env python3
"""
TripAdvisor Session-Based Scraper

This version uses the exact payload structure you discovered:
1. First visits the hotel page to get session cookies
2. Extracts sessionId and pageLoadUid from the page
3. Makes the dual GraphQL requests with proper session data
"""

import re
import json
import time
import uuid
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
import brotli


class TripAdvisorSessionScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.cookies = {}
        self.session_id = None
        self.page_load_uid = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver to get session cookies."""
        try:
            print("Setting up Chrome WebDriver for session extraction...")
            
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Minimal options to avoid detection
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Don't disable too many features to avoid detection
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def extract_session_data(self, url):
        """Extract session cookies and page data from the hotel page."""
        try:
            print(f"Extracting session data from: {url}")
            
            # Navigate to the hotel page
            self.driver.get(url)
            time.sleep(8)  # Wait longer for page to fully load
            
            # Check if we're blocked
            page_source = self.driver.page_source.lower()
            if any(blocked_word in page_source for blocked_word in [
                "unusual activity", "bot activity", "automated", "blocked"
            ]):
                print("❌ Page is blocked - cannot extract session data")
                return False
            
            # Extract cookies
            selenium_cookies = self.driver.get_cookies()
            for cookie in selenium_cookies:
                self.cookies[cookie['name']] = cookie['value']
            
            print(f"Extracted {len(self.cookies)} cookies")
            print(f"Cookie names: {list(self.cookies.keys())}")
            
            # Try to get session data from browser's local storage and session storage
            try:
                # Get session storage
                session_storage = self.driver.execute_script("return window.sessionStorage;")
                print(f"Session storage keys: {list(session_storage.keys()) if session_storage else 'None'}")
                
                # Get local storage
                local_storage = self.driver.execute_script("return window.localStorage;")
                print(f"Local storage keys: {list(local_storage.keys()) if local_storage else 'None'}")
                
            except Exception as e:
                print(f"Could not access storage: {e}")
            
            # Extract sessionId and pageLoadUid from page source or network requests
            page_source = self.driver.page_source
            
            # Look for sessionId in various formats
            session_patterns = [
                r'"sessionId":\s*"([^"]+)"',
                r'sessionId["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'D2855F001712C827E756B613E9303C14',  # Example pattern
                r'[A-F0-9]{32}',  # 32 character hex pattern
            ]
            
            for pattern in session_patterns:
                match = re.search(pattern, page_source)
                if match:
                    self.session_id = match.group(1) if match.groups() else match.group(0)
                    print(f"Found sessionId: {self.session_id}")
                    break
            
            # Look for pageLoadUid
            uid_patterns = [
                r'"pageLoadUid":\s*"([^"]+)"',
                r'pageLoadUid["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',  # UUID pattern
            ]
            
            for pattern in uid_patterns:
                match = re.search(pattern, page_source)
                if match:
                    self.page_load_uid = match.group(1) if match.groups() else match.group(0)
                    print(f"Found pageLoadUid: {self.page_load_uid}")
                    break
            
            # If we can't find them in page source, generate them
            if not self.session_id:
                # Generate a more realistic session ID
                import random
                import string
                self.session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
                print(f"Generated sessionId: {self.session_id}")
            
            if not self.page_load_uid:
                self.page_load_uid = str(uuid.uuid4())
                print(f"Generated pageLoadUid: {self.page_load_uid}")
            
            # Print page title to verify we're on the right page
            print(f"Page title: {self.driver.title}")
            
            return True
            
        except Exception as e:
            print(f"Error extracting session data: {e}")
            return False
    
    def build_payload(self, hotel_id, location_id, check_in_date, check_out_date, adults=2, rooms=1):
        """Build the dual GraphQL payload based on your discovered structure."""
        
        # First query - hotel info and search context
        query1 = {
            "variables": {
                "locationId": location_id,
                "trafficSource": "ba",
                "deviceType": "DESKTOP",
                "servletName": "Hotel_Review",
                "hotelTravelInfo": {
                    "adultCount": adults,
                    "checkInDate": check_in_date,
                    "checkOutDate": check_out_date,
                    "childrenCount": 0,
                    "childAgesPerRoom": "",
                    "roomCount": rooms,
                    "usedDefaultDates": False
                },
                "withContactLinks": False
            },
            "extensions": {
                "preRegisteredQueryId": "d9072109f7378ce1"
            }
        }
        
        # Second query - actual price offers
        query2 = {
            "variables": {
                "request": {
                    "hotelId": hotel_id,
                    "trackingEnabled": True,
                    "requestCaller": "Hotel_Review",
                    "impressionPlacement": "HR_DirectCommerce",
                    "pageLoadUid": self.page_load_uid,
                    "sessionId": self.session_id,
                    "currencyCode": "USD",
                    "requestNumber": 0,
                    "spAttributionToken": None,
                    "shapeStrategy": "DEFAULT_DESKTOP_OFFER_SHAPE",
                    "sequenceId": 0,
                    "travelInfo": {
                        "adults": adults,
                        "rooms": rooms,
                        "checkInDate": check_in_date,
                        "checkOutDate": check_out_date,
                        "childAgesPerRoom": [],
                        "usedDefaultDates": False
                    }
                },
                "locationId": location_id
            },
            "extensions": {
                "preRegisteredQueryId": "1ad9fb68f3f0cdaf"
            }
        }
        
        return [query1, query2]
    
    def make_api_request(self, payload):
        """Make the API request with proper headers and cookies."""
        try:
            url = "https://www.tripadvisor.com/data/graphql/ids"
            
            headers = {
                "X-Tripadvisor-Api-Key": "trip-service-HAC-2021",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Origin": "https://www.tripadvisor.com",
                "Referer": "https://www.tripadvisor.com/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }
            
            print(f"Making API request to: {url}")
            print(f"Using cookies: {list(self.cookies.keys())}")
            print(f"Session ID: {self.session_id}")
            print(f"Page Load UID: {self.page_load_uid}")
            
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                cookies=self.cookies,
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response content length: {len(response.content)}")
            
            if response.status_code == 200:
                if response.content:
                    try:
                        # Check if response is compressed with Brotli
                        content_encoding = response.headers.get('content-encoding', '').lower()
                        print(f"Content encoding: {content_encoding}")
                        
                        if content_encoding == 'br':
                            print("Decompressing Brotli response...")
                            try:
                                # Decompress Brotli content
                                decompressed_content = brotli.decompress(response.content)
                                response_text = decompressed_content.decode('utf-8')
                                print(f"Decompressed content length: {len(response_text)}")
                                return json.loads(response_text)
                            except Exception as brotli_error:
                                print(f"Brotli decompression failed: {brotli_error}")
                                # Fall back to regular response handling
                                return response.json()
                        else:
                            # Regular JSON response
                            return response.json()
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Response encoding: {response.encoding}")
                        print(f"Response headers: {dict(response.headers)}")
                        
                        # Try to get the text content
                        try:
                            text_content = response.text
                            print(f"Text content (first 500 chars): {text_content[:500]}")
                        except Exception as text_error:
                            print(f"Could not get text content: {text_error}")
                        
                        return None
                else:
                    print("Response is empty (no content)")
                    return None
            else:
                print(f"Request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error making API request: {e}")
            return None
    
    def parse_response(self, response_data):
        """Parse the API response to extract pricing information."""
        try:
            if not response_data:
                return None
            
            print("Raw API response:")
            print(json.dumps(response_data, indent=2))
            
            pricing_data = {
                "extracted_at": datetime.now().isoformat(),
                "scraping_method": "session_based_api",
                "raw_response": response_data,
                "prices": [],
                "hotel_info": {},
                "offers": []
            }
            
            # Parse the response structure
            # The response should contain data from both GraphQL queries
            if isinstance(response_data, list) and len(response_data) >= 2:
                # First response - hotel info
                hotel_data = response_data[0].get('data', {})
                if hotel_data:
                    pricing_data["hotel_info"] = hotel_data
                
                # Second response - pricing offers
                offers_data = response_data[1].get('data', {})
                if offers_data:
                    pricing_data["offers"] = offers_data
                    
                    # Extract prices from offers
                    # This will depend on the actual response structure
                    # Look for price-related fields
                    def extract_prices_recursive(obj, path=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if any(price_word in key.lower() for price_word in ['price', 'rate', 'amount', 'cost']):
                                    if isinstance(value, (int, float, str)):
                                        pricing_data["prices"].append({
                                            "field": f"{path}.{key}" if path else key,
                                            "value": value,
                                            "type": type(value).__name__
                                        })
                                extract_prices_recursive(value, f"{path}.{key}" if path else key)
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                extract_prices_recursive(item, f"{path}[{i}]")
                    
                    extract_prices_recursive(offers_data)
            
            print(f"Extracted {len(pricing_data['prices'])} price fields")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None
    
    def scrape_hotel_prices(self, url, check_in_date=None, check_out_date=None, adults=2, rooms=1):
        """Main method to scrape hotel prices using session-based approach."""
        print(f"Starting session-based price scraping for URL: {url}")
        print("=" * 60)
        
        # Parse URL to get hotel ID
        hotel_id_match = re.search(r'-d(\d+)', url)
        if not hotel_id_match:
            print("Error: Could not extract hotel ID from URL")
            return None
        
        hotel_id = int(hotel_id_match.group(1))
        location_id = hotel_id  # Usually the same
        
        # Default dates if not provided
        if not check_in_date:
            check_in_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if not check_out_date:
            check_out_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        print(f"Hotel ID: {hotel_id}")
        print(f"Location ID: {location_id}")
        print(f"Check-in: {check_in_date}")
        print(f"Check-out: {check_out_date}")
        
        # Setup WebDriver
        if not self.setup_driver():
            return None
        
        try:
            # Extract session data
            if not self.extract_session_data(url):
                return None
            
            # Build payload
            payload = self.build_payload(hotel_id, location_id, check_in_date, check_out_date, adults, rooms)
            
            # Make API request
            response_data = self.make_api_request(payload)
            if not response_data:
                return None
            
            # Parse response
            pricing_data = self.parse_response(response_data)
            
            if pricing_data:
                pricing_data["hotel_id"] = hotel_id
                pricing_data["location_id"] = location_id
                pricing_data["travel_params"] = {
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "adults": adults,
                    "rooms": rooms
                }
            
            print("=" * 60)
            print("Session-based scraping completed!")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            return None
        
        finally:
            self.close_driver()


def main():
    """Main function to run the session-based scraper."""
    print("TripAdvisor Session-Based Price Scraper")
    print("=" * 45)
    print("This version uses the exact payload structure you discovered.")
    print("=" * 45)
    
    scraper = TripAdvisorSessionScraper(headless=True)
    
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
        output_file = f"tripadvisor_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pricing_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Display summary
        print(f"\nSession-Based Scraping Summary:")
        print(f"Hotel ID: {pricing_data.get('hotel_id', 'Unknown')}")
        print(f"Prices found: {len(pricing_data.get('prices', []))}")
        print(f"Offers data: {'Yes' if pricing_data.get('offers') else 'No'}")
        
        if pricing_data.get('prices'):
            print("\nPrice fields found:")
            for i, price in enumerate(pricing_data['prices'][:10]):  # Show first 10
                print(f"  {i+1}. {price['field']}: {price['value']} ({price['type']})")
    else:
        print("\nSession-based scraping failed. Check the error messages above.")


if __name__ == "__main__":
    main()

