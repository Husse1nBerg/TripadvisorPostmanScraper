#!/usr/bin/env python3
"""
TripAdvisor Multi-Hotel 90-Day Scraper

This script scrapes 5 Montreal hotels for 90 days each:
1. Vogue Hotel Montreal Downtown (Hilton) - d183258
2. Hotel Le Germain Montreal - d185644  
3. Renaissance Montreal Downtown - d8768071
4. Le Centre Sheraton Montreal - d183253
5. Fairmont the Queen Elizabeth Montreal - d185747
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


class TripAdvisorMultiHotelScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.cookies = {}
        self.session_id = None
        self.page_load_uid = None
        self.all_hotel_offers = {}  # Store offers by hotel
        self.hotels = []  # Will be populated dynamically
    
    def collect_hotel_info(self):
        """Collect hotel information from user input."""
        print("\n🏨 Hotel Information Collection")
        print("=" * 40)
        print("Enter hotel details. Press Enter with empty name to finish.")
        
        hotels = []
        hotel_num = 1
        
        while True:
            print(f"\n--- Hotel {hotel_num} ---")
            
            # Get hotel name
            hotel_name = input("Hotel name: ").strip()
            if not hotel_name:
                break
            
            # Get g code (location ID)
            while True:
                g_code = input("G code (location ID, e.g., 155032): ").strip()
                if g_code.isdigit():
                    g_code = int(g_code)
                    break
                print("Please enter a valid number for G code.")
            
            # Get d code (hotel ID)
            while True:
                d_code = input("D code (hotel ID, e.g., 183258): ").strip()
                if d_code.isdigit():
                    d_code = int(d_code)
                    break
                print("Please enter a valid number for D code.")
            
            # Build URL
            url = f"https://www.tripadvisor.com/Hotel_Review-g{g_code}-d{d_code}-Reviews-{hotel_name.replace(' ', '_')}-Montreal_Quebec.html"
            
            hotel_info = {
                "name": hotel_name,
                "hotel_id": d_code,
                "location_id": g_code,
                "url": url
            }
            
            hotels.append(hotel_info)
            print(f"✅ Added: {hotel_name} (G:{g_code}, D:{d_code})")
            
            hotel_num += 1
        
        if not hotels:
            print("No hotels added. Exiting.")
            return None
        
        print(f"\n📋 Summary: {len(hotels)} hotels added")
        for i, hotel in enumerate(hotels, 1):
            print(f"   {i}. {hotel['name']} (G:{hotel['location_id']}, D:{hotel['hotel_id']})")
        
        return hotels
    
    def get_scraping_parameters(self):
        """Get scraping parameters from user."""
        print("\n📅 Scraping Parameters")
        print("=" * 30)
        
        # Get number of days
        while True:
            days_input = input("Number of days to scrape [default: 90]: ").strip()
            if not days_input:
                num_days = 90
                break
            try:
                num_days = int(days_input)
                if num_days > 0:
                    break
                print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Get travel parameters
        while True:
            adults_input = input("Number of adults [default: 2]: ").strip()
            if not adults_input:
                adults = 2
                break
            try:
                adults = int(adults_input)
                if adults > 0:
                    break
                print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")
        
        while True:
            rooms_input = input("Number of rooms [default: 1]: ").strip()
            if not rooms_input:
                rooms = 1
                break
            try:
                rooms = int(rooms_input)
                if rooms > 0:
                    break
                print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")
        
        return num_days, adults, rooms
        
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
    
    def parse_offers_from_response(self, response_data, hotel_name, check_in_date, check_out_date):
        """Parse offers from the API response."""
        offers = []
        
        if not isinstance(response_data, list) or len(response_data) < 2:
            return offers

        offers_data = response_data[1].get("data", {})
        
        # Look specifically in HPS_getWebHROffers for chevronOffers and hiddenOffers
        hps_offers = offers_data.get("HPS_getWebHROffers", {})
        
        # Check chevronOffers
        chevron_offers = hps_offers.get("chevronOffers", [])
        for offer in chevron_offers:
            if isinstance(offer, dict) and 'data' in offer:
                data_atts = offer.get("data", {})
                if 'dataAtts' in data_atts:
                    data_atts = data_atts.get("dataAtts", {})
                    provider = data_atts.get("provider")
                    price = data_atts.get("totalPrice") or data_atts.get("perNight")
                    if provider and price is not None:
                        try:
                            offers.append({
                                "ota_name": provider,
                                "hotel_name": hotel_name,
                                "location_code": data_atts.get('locationId'),
                                "hotel_id": data_atts.get('locationId'),
                                "currency": "USD",
                                "base_price": data_atts.get("perNight"),
                                "tax": data_atts.get("taxesValue"),
                                "total_price": float(price),
                                "price_per_night": data_atts.get("perNight"),
                                "check_in_date": check_in_date,
                                "check_out_date": check_out_date,
                                "adults": 2,
                                "rooms": 1,
                                "children": 0,
                                "occupants": 2,
                                "extracted_at": datetime.now().isoformat()
                            })
                        except (ValueError, TypeError):
                            pass
        
        # Check hiddenOffers
        hidden_offers = hps_offers.get("hiddenOffers", [])
        for offer in hidden_offers:
            if isinstance(offer, dict) and 'data' in offer:
                data_atts = offer.get("data", {})
                if 'dataAtts' in data_atts:
                    data_atts = data_atts.get("dataAt", {})
                    provider = data_atts.get("provider")
                    price = data_atts.get("totalPrice") or data_atts.get("perNight")
                    if provider and price is not None:
                        try:
                            offers.append({
                                "ota_name": provider,
                                "hotel_name": hotel_name,
                                "location_code": data_atts.get('locationId'),
                                "hotel_id": data_atts.get('locationId'),
                                "currency": "USD",
                                "base_price": data_atts.get("perNight"),
                                "tax": data_atts.get("taxesValue"),
                                "total_price": float(price),
                                "price_per_night": data_atts.get("perNight"),
                                "check_in_date": check_in_date,
                                "check_out_date": check_out_date,
                                "adults": 2,
                                "rooms": 1,
                                "children": 0,
                                "occupants": 2,
                                "extracted_at": datetime.now().isoformat()
                            })
                        except (ValueError, TypeError):
                            pass
        
        return offers
    
    def scrape_hotel_days(self, hotel, num_days, adults=2, rooms=1):
        """Scrape prices for a single hotel for specified number of days."""
        print(f"\n🏨 Starting {num_days}-day scraping for: {hotel['name']}")
        print(f"Hotel ID: {hotel['hotel_id']}")
        print("=" * 80)
        
        hotel_offers = []
        
        # Extract session data (only once per hotel)
        if not self.extract_session_data(hotel['url']):
            print(f"❌ Failed to extract session data for {hotel['name']}")
            return hotel_offers
        
        # Scrape for specified number of days
        start_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
        
        for day in range(num_days):
            check_in_date = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
            check_out_date = (start_date + timedelta(days=day + 1)).strftime("%Y-%m-%d")
            
            print(f"  Day {day + 1}/{num_days} | {check_in_date}...", end=" ")
            
            # Build payload for this specific date
            payload = self.build_payload(
                hotel['hotel_id'], 
                hotel['location_id'], 
                check_in_date, 
                check_out_date, 
                adults, 
                rooms
            )
            
            # Make API request
            response_data = self.make_api_request(payload)
            
            if response_data:
                # Parse offers
                day_offers = self.parse_offers_from_response(
                    response_data, 
                    hotel['name'], 
                    check_in_date, 
                    check_out_date
                )
                
                if day_offers:
                    print(f"✅ {len(day_offers)} offers")
                    hotel_offers.extend(day_offers)
                else:
                    print("⚠️ No offers")
            else:
                print("❌ No response")
            
            # Small delay between requests
            time.sleep(1)
        
        print(f"\n🎉 Completed {hotel['name']}: {len(hotel_offers)} total offers")
        return hotel_offers
    
    def scrape_all_hotels(self, num_days, adults=2, rooms=1):
        """Scrape all hotels for specified number of days each."""
        print("🚀 TripAdvisor Multi-Hotel Scraper")
        print("=" * 60)
        print(f"Scraping {len(self.hotels)} hotels for {num_days} days each")
        print(f"Total expected requests: {len(self.hotels) * num_days}")
        print("=" * 60)
        
        # Setup WebDriver
        if not self.setup_driver():
            return None
        
        try:
            all_results = {}
            total_offers = 0
            
            for i, hotel in enumerate(self.hotels, 1):
                print(f"\n🏨 Hotel {i}/{len(self.hotels)}: {hotel['name']}")
                
                # Scrape this hotel
                hotel_offers = self.scrape_hotel_days(hotel, num_days, adults, rooms)
                
                # Store results
                all_results[hotel['name']] = {
                    "hotel_info": hotel,
                    "offers": hotel_offers,
                    "total_offers": len(hotel_offers)
                }
                
                total_offers += len(hotel_offers)
                
                # Progress update
                print(f"\n📊 Progress: {i}/{len(self.hotels)} hotels completed")
                print(f"Total offers so far: {total_offers}")
                
                # Longer delay between hotels to avoid rate limiting
                if i < len(self.hotels):
                    print("⏳ Waiting 30 seconds before next hotel...")
                    time.sleep(30)
            
            print(f"\n🎉 ALL HOTELS COMPLETED!")
            print(f"Total offers collected: {total_offers}")
            
            return {
                "extracted_at": datetime.now().isoformat(),
                "scraping_method": "multi_hotel_90_day",
                "total_hotels": len(self.hotels),
                "total_offers": total_offers,
                "hotels": all_results
            }
            
        except Exception as e:
            print(f"Error during multi-hotel scraping: {e}")
            return None
        
        finally:
            self.close_driver()
    
    def export_to_csv(self, all_results, filename=None):
        """Export all hotel offers to a single CSV file."""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"tripadvisor_5hotels_90days_{timestamp}.csv"
            
            # Collect all offers from all hotels
            all_offers = []
            for hotel_name, hotel_data in all_results.get('hotels', {}).items():
                for offer in hotel_data.get('offers', []):
                    all_offers.append(offer)
            
            if not all_offers:
                print("No offers to export")
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
                
                for offer in all_offers:
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
                        'Extracted_At': offer.get('extracted_at', '')
                    }
                    writer.writerow(row)
            
            print(f"✅ Exported {len(all_offers)} offers from {len(all_results.get('hotels', {}))} hotels to: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None


def main():
    """Main function to run the multi-hotel scraper."""
    print("TripAdvisor Multi-Hotel Price Scraper")
    print("=" * 50)
    print("This will scrape any number of hotels for any number of days.")
    print("=" * 50)
    
    scraper = TripAdvisorMultiHotelScraper(headless=True)
    
    # Collect hotel information
    hotels = scraper.collect_hotel_info()
    if not hotels:
        return
    
    # Get scraping parameters
    num_days, adults, rooms = scraper.get_scraping_parameters()
    
    # Set hotels in scraper
    scraper.hotels = hotels
    
    # Confirm before starting
    print(f"\n🚀 Ready to scrape:")
    print(f"   • {len(hotels)} hotels")
    print(f"   • {num_days} days each")
    print(f"   • {adults} adults, {rooms} room(s)")
    print(f"   • Total: {len(hotels) * num_days} API requests")
    
    # Estimate runtime
    estimated_hours = (len(hotels) * num_days * 2) / 60  # 2 seconds per request + delays
    print(f"   • Estimated runtime: {estimated_hours:.1f} hours")
    
    confirm = input("\nStart scraping? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Scraping cancelled.")
        return
    
    # Scrape all hotels
    all_results = scraper.scrape_all_hotels(num_days, adults, rooms)
    
    if all_results:
        # Save JSON results
        json_file = f"tripadvisor_{len(hotels)}hotels_{num_days}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\nJSON results saved to: {json_file}")
        
        # Export to CSV
        csv_file = scraper.export_to_csv(all_results)
        
        # Display summary
        print(f"\n📊 Multi-Hotel Scraping Summary:")
        print(f"Hotels scraped: {all_results.get('total_hotels', 0)}")
        print(f"Days per hotel: {num_days}")
        print(f"Total offers found: {all_results.get('total_offers', 0)}")
        
        print(f"\n🏨 Per-Hotel Results:")
        for hotel_name, hotel_data in all_results.get('hotels', {}).items():
            print(f"   • {hotel_name}: {hotel_data.get('total_offers', 0)} offers")
        
        if csv_file:
            print(f"\n📊 CSV Export:")
            print(f"   File: {csv_file}")
            print(f"   Ready for Excel/Google Sheets import!")
        
    else:
        print("\nMulti-hotel scraping failed. Check the error messages above.")


if __name__ == "__main__":
    main()
