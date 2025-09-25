#!/usr/bin/env python3
"""
TripAdvisor 90-Day Scraper

This version scrapes hotel prices for 90 days ahead and includes
enhanced debugging to understand why offers aren't being found.
"""

import re
import json
import time
import uuid
import csv
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


class TripAdvisor90DayScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.cookies = {}
        self.session_id = None
        self.page_load_uid = None
        self.all_offers = []  # Store all offers from all days
        
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
            
            # Extract sessionId and pageLoadUid from page source
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
                import random
                import string
                self.session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
                print(f"Generated sessionId: {self.session_id}")
            
            if not self.page_load_uid:
                self.page_load_uid = str(uuid.uuid4())
                print(f"Generated pageLoadUid: {self.page_load_uid}")
            
            print(f"Page title: {self.driver.title}")
            return True
            
        except Exception as e:
            print(f"Error extracting session data: {e}")
            return False
    
    def build_payload(self, hotel_id, location_id, check_in_date, check_out_date, adults=2, rooms=1):
        """Build the dual GraphQL payload."""
        
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
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }
            
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                cookies=self.cookies,
                timeout=30
            )
            
            if response.status_code == 200:
                if response.content:
                    try:
                        content_encoding = response.headers.get('content-encoding', '').lower()
                        
                        if content_encoding == 'br':
                            try:
                                decompressed_content = brotli.decompress(response.content)
                                response_text = decompressed_content.decode('utf-8')
                                return json.loads(response_text)
                            except Exception as brotli_error:
                                print(f"Brotli decompression failed: {brotli_error}")
                                try:
                                    response.raw.decode_content = True
                                    response_text = response.text
                                    return json.loads(response_text)
                                except Exception as alt_error:
                                    print(f"Alternative decompression failed: {alt_error}")
                                    return None
                        else:
                            return response.json()
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        return None
                else:
                    print("Response is empty (no content)")
                    return None
            else:
                print(f"Request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error making API request: {e}")
            return None
    
    def debug_response_structure(self, response_data, day_num):
        """Debug the response structure to understand why offers aren't found."""
        print(f"\n🔍 DEBUGGING Day {day_num} Response Structure:")
        print("=" * 50)
        
        if not response_data:
            print("❌ No response data")
            return []
        
        if isinstance(response_data, list):
            print(f"📋 Response is a list with {len(response_data)} items")
            for i, item in enumerate(response_data):
                print(f"  Item {i}: {type(item)}")
                if isinstance(item, dict):
                    print(f"    Keys: {list(item.keys())}")
                    if 'data' in item:
                        data = item['data']
                        print(f"    Data type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"    Data keys: {list(data.keys())}")
        else:
            print(f"📋 Response is: {type(response_data)}")
            if isinstance(response_data, dict):
                print(f"  Keys: {list(response_data.keys())}")
        
        # Try to find any offers in the response
        offers_found = self.find_offers_in_response(response_data)
        print(f"🎯 Found {len(offers_found)} potential offers in response")
        
        return offers_found
    
    def find_offers_in_response(self, response_data):
        """Find any potential offers in the response data."""
        offers = []
        
        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                # Look for objects that might be offers
                if 'dataAtts' in obj and isinstance(obj['dataAtts'], dict):
                    data_atts = obj['dataAtts']
                    if 'provider' in data_atts or 'vendorName' in data_atts:
                        offers.append({
                            'path': path,
                            'data': obj,
                            'provider': data_atts.get('provider'),
                            'vendor': data_atts.get('vendorName')
                        })
                        print(f"  ✅ Found potential offer at {path}: {data_atts.get('provider', data_atts.get('vendorName'))}")
                
                # Continue searching
                for key, value in obj.items():
                    search_recursive(value, f"{path}.{key}" if path else key)
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_recursive(item, f"{path}[{i}]")
        
        search_recursive(response_data)
        return offers
    
    def parse_offer_from_debug(self, offer_data, check_in_date, check_out_date):
        """Parse an offer found during debugging."""
        try:
            if 'dataAtts' not in offer_data:
                return None
            
            data_atts = offer_data['dataAtts']
            ota_name = data_atts.get('provider') or data_atts.get('vendorName')
            
            if not ota_name:
                return None
            
            # Extract pricing
            base_price = data_atts.get('perNight')
            tax = data_atts.get('taxesValue')
            total_price = None
            
            if base_price and tax:
                try:
                    total_price = float(base_price) + float(tax)
                except (ValueError, TypeError):
                    pass
            
            return {
                "ota_name": ota_name,
                "hotel_name": "Unknown",  # We'll need to get this from elsewhere
                "location_code": data_atts.get('locationId'),
                "hotel_id": data_atts.get('locationId'),  # Assuming same as location
                "currency": "USD",
                "base_price": base_price,
                "tax": tax,
                "total_price": total_price,
                "price_per_night": base_price,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": 2,  # Default
                "rooms": 1,   # Default
                "children": 0,
                "occupants": 2,
                "raw_offer": offer_data
            }
            
        except Exception as e:
            print(f"Error parsing offer: {e}")
            return None
    
    def scrape_single_day(self, hotel_id, location_id, check_in_date, check_out_date, day_num, total_days):
        """Scrape prices for a single day."""
        print(f"\nScraping Day {day_num}/{total_days} | Check-in: {check_in_date}...")
        
        # Build payload for this specific date
        payload = self.build_payload(hotel_id, location_id, check_in_date, check_out_date)
        
        # Make API request
        response_data = self.make_api_request(payload)
        
        if not response_data:
            print(f"  ❌ No response for day {day_num}")
            return []
        
        # Debug the response structure
        offers_found = self.debug_response_structure(response_data, day_num)
        
        # Parse offers
        parsed_offers = []
        for offer_data in offers_found:
            parsed_offer = self.parse_offer_from_debug(offer_data['data'], check_in_date, check_out_date)
            if parsed_offer:
                parsed_offers.append(parsed_offer)
        
        if parsed_offers:
            print(f"  ✅ Found {len(parsed_offers)} valid offers for day {day_num}")
        else:
            print(f"  ⚠️ API response received, but no valid offers found inside.")
        
        return parsed_offers
    
    def scrape_90_days(self, url, adults=2, rooms=1):
        """Scrape prices for 90 days ahead."""
        print(f"Starting 90-day price scraping for URL: {url}")
        print("=" * 60)
        
        # Parse URL to get hotel ID
        hotel_id_match = re.search(r'-d(\d+)', url)
        if not hotel_id_match:
            print("Error: Could not extract hotel ID from URL")
            return None
        
        hotel_id = int(hotel_id_match.group(1))
        location_id = hotel_id  # Usually the same
        
        print(f"Hotel ID: {hotel_id}")
        print(f"Location ID: {location_id}")
        
        # Setup WebDriver and extract session data
        if not self.setup_driver():
            return None
        
        try:
            # Extract session data (only once)
            if not self.extract_session_data(url):
                return None
            
            # Scrape for 90 days
            start_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
            
            for day in range(90):
                check_in_date = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
                check_out_date = (start_date + timedelta(days=day + 1)).strftime("%Y-%m-%d")
                
                # Scrape this day
                day_offers = self.scrape_single_day(
                    hotel_id, location_id, check_in_date, check_out_date, day + 1, 90
                )
                
                # Add to all offers
                self.all_offers.extend(day_offers)
                
                # Small delay between requests
                time.sleep(1)
            
            print(f"\n🎉 90-day scraping completed!")
            print(f"Total offers found: {len(self.all_offers)}")
            
            return {
                "extracted_at": datetime.now().isoformat(),
                "scraping_method": "90_day_session_based",
                "hotel_id": hotel_id,
                "location_id": location_id,
                "total_days_scraped": 90,
                "total_offers_found": len(self.all_offers),
                "ota_offers": self.all_offers
            }
            
        except Exception as e:
            print(f"Error during 90-day scraping: {e}")
            return None
        
        finally:
            self.close_driver()
    
    def export_to_csv(self, pricing_data, filename=None):
        """Export all offers to CSV file."""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"tripadvisor_90day_offers_{timestamp}.csv"
            
            ota_offers = pricing_data.get('ota_offers', [])
            if not ota_offers:
                print("No OTA offers to export")
                return None
            
            headers = [
                'OTA_Name', 'Hotel_Name', 'Location_Code_G', 'Hotel_ID_D',
                'Currency', 'Base_Price', 'Tax', 'Total_Price', 'Price_Per_Night',
                'Check_In_Date', 'Check_Out_Date', 'Adults', 'Children',
                'Occupants', 'Rooms', 'Extracted_At'
            ]
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for offer in ota_offers:
                    row = {
                        'OTA_Name': offer.get('ota_name', ''),
                        'Hotel_Name': offer.get('hotel_name', ''),
                        'Location_Code_G': offer.get('location_code', ''),
                        'Hotel_ID_D': offer.get('hotel_id', ''),
                        'Currency': offer.get('currency', ''),
                        'Base_Price': offer.get('base_price', ''),
                        'Tax': offer.get('tax', ''),
                        'Total_Price': offer.get('total_price', ''),
                        'Price_Per_Night': offer.get('price_per_night', ''),
                        'Check_In_Date': offer.get('check_in_date', ''),
                        'Check_Out_Date': offer.get('check_out_date', ''),
                        'Adults': offer.get('adults', ''),
                        'Children': offer.get('children', ''),
                        'Occupants': offer.get('occupants', ''),
                        'Rooms': offer.get('rooms', ''),
                        'Extracted_At': pricing_data.get('extracted_at', '')
                    }
                    writer.writerow(row)
            
            print(f"✅ Exported {len(ota_offers)} OTA offers to: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None


def main():
    """Main function to run the 90-day scraper."""
    print("TripAdvisor 90-Day Price Scraper")
    print("=" * 40)
    print("This will scrape prices for 90 days ahead with enhanced debugging.")
    print("=" * 40)
    
    scraper = TripAdvisor90DayScraper(headless=True)
    
    # Get URL from user
    url = input("Enter TripAdvisor hotel URL: ").strip()
    if not url:
        print("Error: No URL provided")
        return
    
    # Optional travel parameters
    print("\nOptional travel parameters (press Enter for defaults):")
    adults_input = input("Number of adults [default: 2]: ").strip()
    adults = int(adults_input) if adults_input.isdigit() else 2
    rooms_input = input("Number of rooms [default: 1]: ").strip()
    rooms = int(rooms_input) if rooms_input.isdigit() else 1
    
    # Scrape for 90 days
    pricing_data = scraper.scrape_90_days(url, adults, rooms)
    
    if pricing_data:
        # Save JSON results
        json_file = f"tripadvisor_90day_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(pricing_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nJSON results saved to: {json_file}")
        
        # Export to CSV
        csv_file = scraper.export_to_csv(pricing_data)
        
        # Display summary
        print(f"\n90-Day Scraping Summary:")
        print(f"Hotel ID: {pricing_data.get('hotel_id', 'Unknown')}")
        print(f"Days scraped: {pricing_data.get('total_days_scraped', 0)}")
        print(f"Total offers found: {pricing_data.get('total_offers_found', 0)}")
        
        if csv_file:
            print(f"\n📊 CSV Export:")
            print(f"   File: {csv_file}")
            print(f"   Ready for Excel/Google Sheets import!")
        
    else:
        print("\n90-day scraping failed. Check the error messages above.")


if __name__ == "__main__":
    main()
