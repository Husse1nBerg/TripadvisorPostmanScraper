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
                "Accept-Encoding": "gzip, deflate",  # Remove 'br' to avoid Brotli compression
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
                                print("Trying alternative decompression methods...")
                                
                                # Try using requests' built-in decompression
                                try:
                                    # Force requests to handle decompression
                                    response.raw.decode_content = True
                                    response_text = response.text
                                    print(f"Alternative decompression successful, length: {len(response_text)}")
                                    return json.loads(response_text)
                                except Exception as alt_error:
                                    print(f"Alternative decompression failed: {alt_error}")
                                    
                                    # Try manual gzip decompression (sometimes Brotli is mislabeled)
                                    try:
                                        import gzip
                                        decompressed_content = gzip.decompress(response.content)
                                        response_text = decompressed_content.decode('utf-8')
                                        print(f"Gzip decompression successful, length: {len(response_text)}")
                                        return json.loads(response_text)
                                    except Exception as gzip_error:
                                        print(f"Gzip decompression failed: {gzip_error}")
                                        
                                        # Last resort: try to parse as-is
                                        try:
                                            response_text = response.content.decode('utf-8', errors='ignore')
                                            print(f"Raw decode successful, length: {len(response_text)}")
                                            return json.loads(response_text)
                                        except Exception as raw_error:
                                            print(f"Raw decode failed: {raw_error}")
                                            return None
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
                "ota_offers": [],  # Online Travel Agency offers
                "hotel_info": {},
                "prices": []
            }
            
            # Parse the response structure
            if isinstance(response_data, list) and len(response_data) >= 2:
                # First response - hotel info
                hotel_data = response_data[0].get('data', {})
                if hotel_data:
                    pricing_data["hotel_info"] = hotel_data
                
                # Second response - pricing offers
                offers_data = response_data[1].get('data', {})
                if offers_data:
                    pricing_data["offers"] = offers_data
                    
                    # Extract OTA offers from the response
                    ota_offers = self.extract_ota_offers(offers_data)
                    pricing_data["ota_offers"] = ota_offers
                    
                    print(f"Extracted {len(ota_offers)} OTA offers")
            
            return pricing_data
            
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None
    
    def extract_ota_offers(self, offers_data):
        """Extract Online Travel Agency offers from the response data."""
        ota_offers = []
        
        try:
            print("Searching for OTA offers in response data...")
            
            # Based on the terminal output, the structure seems to be in the second GraphQL response
            # Let's look for the actual structure from the terminal output
            
            def find_offers_recursive(obj, path=""):
                if isinstance(obj, dict):
                    # Look for the specific structure we saw in the terminal
                    if 'dataAtts' in obj and 'provider' in obj.get('dataAtts', {}):
                        # This looks like an offer object
                        ota_offer = self.parse_single_offer(obj)
                        if ota_offer:
                            ota_offers.append(ota_offer)
                            print(f"Found offer from {ota_offer.get('ota_name')} at path: {path}")
                    
                    # Also look for arrays that might contain offers
                    for key, value in obj.items():
                        if isinstance(value, list) and key in ['offers', 'providers', 'bookingOptions', 'rates', 'prices', 'results']:
                            print(f"Found potential offers array at: {path}.{key} with {len(value)} items")
                            for i, item in enumerate(value):
                                if isinstance(item, dict):
                                    ota_offer = self.parse_single_offer(item)
                                    if ota_offer:
                                        ota_offers.append(ota_offer)
                                        print(f"Found offer from {ota_offer.get('ota_name')} at path: {path}.{key}[{i}]")
                        
                        # Continue searching recursively
                        find_offers_recursive(value, f"{path}.{key}" if path else key)
                        
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_offers_recursive(item, f"{path}[{i}]")
            
            find_offers_recursive(offers_data)
            
            # If still no offers found, try to extract from the raw response structure
            if not ota_offers:
                print("No offers found in recursive search, trying raw response extraction...")
                ota_offers = self.extract_from_raw_response(offers_data)
            
            print(f"Total OTA offers found: {len(ota_offers)}")
            return ota_offers
            
        except Exception as e:
            print(f"Error extracting OTA offers: {e}")
            return []
    
    def parse_single_offer(self, offer_data):
        """Parse a single offer to extract OTA information."""
        try:
            # Extract OTA name
            ota_name = self.extract_ota_name(offer_data)
            if not ota_name:
                return None
            
            # Extract pricing information
            price_info = self.extract_price_info(offer_data)
            
            # Extract travel information
            travel_info = self.extract_travel_info(offer_data)
            
            # Extract hotel information
            hotel_info = self.extract_hotel_info(offer_data)
            
            # Combine all information
            ota_offer = {
                "ota_name": ota_name,
                "hotel_name": hotel_info.get("hotel_name"),
                "location_code": hotel_info.get("location_code"),  # g code
                "hotel_id": hotel_info.get("hotel_id"),  # d code
                "currency": price_info.get("currency", "USD"),
                "base_price": price_info.get("base_price"),
                "tax": price_info.get("tax"),
                "total_price": price_info.get("total_price"),
                "price_per_night": price_info.get("price_per_night"),
                "check_in_date": travel_info.get("check_in_date"),
                "check_out_date": travel_info.get("check_out_date"),
                "adults": travel_info.get("adults"),
                "rooms": travel_info.get("rooms"),
                "children": travel_info.get("children"),
                "occupants": travel_info.get("adults", 0) + travel_info.get("children", 0),  # Total occupants
                "raw_offer": offer_data  # Keep raw data for debugging
            }
            
            return ota_offer
            
        except Exception as e:
            print(f"Error parsing single offer: {e}")
            return None
    
    def extract_ota_name(self, offer_data):
        """Extract the Online Travel Agency name from offer data."""
        # Based on the terminal output, the structure is: dataAtts.provider
        if 'dataAtts' in offer_data and isinstance(offer_data['dataAtts'], dict):
            provider = offer_data['dataAtts'].get('provider')
            if provider:
                return provider.strip()
        
        # Also check vendorName from dataAtts
        if 'dataAtts' in offer_data and isinstance(offer_data['dataAtts'], dict):
            vendor_name = offer_data['dataAtts'].get('vendorName')
            if vendor_name:
                return vendor_name.strip()
        
        # Common OTA name fields (fallback)
        ota_fields = [
            'provider', 'providerName', 'ota', 'otaName', 'bookingSite', 
            'site', 'source', 'vendor', 'supplier', 'name', 'title'
        ]
        
        for field in ota_fields:
            if field in offer_data:
                ota_name = offer_data[field]
                if isinstance(ota_name, str) and ota_name.strip():
                    return ota_name.strip()
        
        # Try to extract from URL or other fields
        if 'url' in offer_data:
            url = offer_data['url']
            if 'expedia' in url.lower():
                return 'Expedia'
            elif 'booking' in url.lower():
                return 'Booking.com'
            elif 'hotels' in url.lower():
                return 'Hotels.com'
            elif 'agoda' in url.lower():
                return 'Agoda'
            elif 'priceline' in url.lower():
                return 'Priceline'
        
        return None
    
    def extract_price_info(self, offer_data):
        """Extract pricing information from offer data."""
        price_info = {}
        
        # Based on the terminal output, the structure is in dataAtts
        if 'dataAtts' in offer_data and isinstance(offer_data['dataAtts'], dict):
            data_atts = offer_data['dataAtts']
            
            # Extract perNight and taxesValue from dataAt
            if 'perNight' in data_atts:
                price_info['price_per_night'] = data_atts['perNight']
                price_info['base_price'] = data_atts['perNight']  # Use perNight as base price
            
            if 'taxesValue' in data_atts:
                price_info['tax'] = data_atts['taxesValue']
            
            # Calculate total price if we have base and tax
            if 'perNight' in data_atts and 'taxesValue' in data_atts:
                try:
                    base = float(data_atts['perNight'])
                    tax = float(data_atts['taxesValue'])
                    price_info['total_price'] = base + tax
                except (ValueError, TypeError):
                    pass
        
        # Also check common price fields (fallback)
        price_fields = {
            'base_price': ['price', 'basePrice', 'rate', 'baseRate', 'amount', 'baseAmount'],
            'total_price': ['totalPrice', 'total', 'totalAmount', 'grandTotal'],
            'tax': ['tax', 'taxes', 'taxAmount', 'fees'],
            'currency': ['currency', 'currencyCode', 'currency_code'],
            'price_per_night': ['pricePerNight', 'perNight', 'nightlyRate']
        }
        
        for price_type, fields in price_fields.items():
            if price_type not in price_info:  # Only if not already found in dataAtts
                for field in fields:
                    if field in offer_data:
                        value = offer_data[field]
                        if value is not None:
                            price_info[price_type] = value
                            break
        
        # Default currency if not found
        if 'currency' not in price_info:
            price_info['currency'] = 'USD'
        
        return price_info
    
    def extract_travel_info(self, offer_data):
        """Extract travel information from offer data."""
        travel_info = {}
        
        # Based on the terminal output, travel info might be in searchParameters
        if 'searchParameters' in offer_data and isinstance(offer_data['searchParameters'], dict):
            search_params = offer_data['searchParameters']
            if 'travelInfo' in search_params and isinstance(search_params['travelInfo'], dict):
                travel_data = search_params['travelInfo']
                
                travel_info['check_in_date'] = travel_data.get('checkInDate')
                travel_info['check_out_date'] = travel_data.get('checkOutDate')
                travel_info['adults'] = travel_data.get('adults')
                travel_info['rooms'] = travel_data.get('rooms')
                travel_info['children'] = len(travel_data.get('childAgesPerRoom', []))
        
        # Common travel fields (fallback)
        travel_fields = {
            'check_in_date': ['checkInDate', 'checkin', 'arrival'],
            'check_out_date': ['checkOutDate', 'checkout', 'departure'],
            'adults': ['adults', 'adultCount', 'guests'],
            'rooms': ['rooms', 'roomCount', 'room_count'],
            'children': ['children', 'childCount', 'childrenCount']
        }
        
        for travel_type, fields in travel_fields.items():
            if travel_type not in travel_info:  # Only if not already found
                for field in fields:
                    if field in offer_data:
                        value = offer_data[field]
                        if value is not None:
                            travel_info[travel_type] = value
                            break
        
        return travel_info
    
    def extract_hotel_info(self, offer_data):
        """Extract hotel information from offer data."""
        hotel_info = {}
        
        # Extract from dataAtts if available
        if 'dataAt' in offer_data and isinstance(offer_data['dataAt'], dict):
            data_atts = offer_data['dataAt']
            
            # Extract location ID (g code)
            if 'locationId' in data_atts:
                hotel_info['location_code'] = data_atts['locationId']
        
        # Try to extract hotel name from various sources
        hotel_name_fields = [
            'hotelName', 'hotel_name', 'name', 'title', 'propertyName', 'property_name'
        ]
        
        for field in hotel_name_fields:
            if field in offer_data:
                hotel_name = offer_data[field]
                if isinstance(hotel_name, str) and hotel_name.strip():
                    hotel_info['hotel_name'] = hotel_name.strip()
                    break
        
        # Extract hotel ID (d code) from various sources
        hotel_id_fields = [
            'hotelId', 'hotel_id', 'propertyId', 'property_id', 'id'
        ]
        
        for field in hotel_id_fields:
            if field in offer_data:
                hotel_id = offer_data[field]
                if hotel_id is not None:
                    hotel_info['hotel_id'] = hotel_id
                    break
        
        return hotel_info
    
    def extract_from_raw_response(self, offers_data):
        """Extract offers from the raw response structure."""
        ota_offers = []
        
        try:
            print("Attempting to extract from raw response structure...")
            
            # Print the structure to understand it better
            print("Response structure keys:", list(offers_data.keys()) if isinstance(offers_data, dict) else "Not a dict")
            
            # Look for the specific structure we saw in the terminal
            # The data seems to be in the second GraphQL response
            if isinstance(offers_data, dict):
                # Try to find offers in various possible locations
                possible_locations = [
                    'data',
                    'hotelOffers',
                    'offers',
                    'results',
                    'rates',
                    'prices'
                ]
                
                for location in possible_locations:
                    if location in offers_data:
                        print(f"Found data at: {location}")
                        data = offers_data[location]
                        
                        if isinstance(data, list):
                            print(f"Found list with {len(data)} items at {location}")
                            for i, item in enumerate(data):
                                if isinstance(item, dict):
                                    ota_offer = self.parse_single_offer(item)
                                    if ota_offer:
                                        ota_offers.append(ota_offer)
                                        print(f"Extracted offer from {ota_offer.get('ota_name')}")
                        elif isinstance(data, dict):
                            # Recursively search in this dict
                            ota_offers.extend(self.extract_from_raw_response(data))
            
            return ota_offers
            
        except Exception as e:
            print(f"Error in raw response extraction: {e}")
            return []
    
    def try_common_offer_patterns(self, offers_data):
        """Try common patterns to find offers in the response."""
        ota_offers = []
        
        # Try different common response structures
        patterns = [
            'data.hotelOffers.offers',
            'data.offers',
            'data.rates',
            'data.prices',
            'data.bookingOptions',
            'data.providers'
        ]
        
        for pattern in patterns:
            try:
                # Navigate to the pattern
                current = offers_data
                for key in pattern.split('.'):
                    if key in current:
                        current = current[key]
                    else:
                        current = None
                        break
                
                if current and isinstance(current, list):
                    for item in current:
                        if isinstance(item, dict):
                            ota_offer = self.parse_single_offer(item)
                            if ota_offer:
                                ota_offers.append(ota_offer)
            except Exception:
                continue
        
        return ota_offers
    
    def export_to_csv(self, pricing_data, filename=None):
        """Export OTA offers to CSV file."""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"tripadvisor_ota_offers_{timestamp}.csv"
            
            ota_offers = pricing_data.get('ota_offers', [])
            if not ota_offers:
                print("No OTA offers to export")
                return None
            
            # Define CSV headers
            headers = [
                'OTA_Name',
                'Hotel_Name',
                'Location_Code_G',
                'Hotel_ID_D',
                'Currency',
                'Base_Price',
                'Tax',
                'Total_Price',
                'Price_Per_Night',
                'Check_In_Date',
                'Check_Out_Date',
                'Adults',
                'Children',
                'Occupants',
                'Rooms',
                'Extracted_At'
            ]
            
            # Write to CSV
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
    
    def create_ota_summary(self, pricing_data):
        """Create a summary of OTA offers grouped by agency."""
        try:
            ota_offers = pricing_data.get('ota_offers', [])
            if not ota_offers:
                return {}
            
            # Group offers by OTA
            ota_summary = {}
            for offer in ota_offers:
                ota_name = offer.get('ota_name', 'Unknown')
                if ota_name not in ota_summary:
                    ota_summary[ota_name] = {
                        'count': 0,
                        'offers': [],
                        'min_price': float('inf'),
                        'max_price': 0,
                        'avg_price': 0
                    }
                
                ota_summary[ota_name]['count'] += 1
                ota_summary[ota_name]['offers'].append(offer)
                
                # Calculate price statistics
                total_price = offer.get('total_price')
                if total_price and isinstance(total_price, (int, float)):
                    ota_summary[ota_name]['min_price'] = min(ota_summary[ota_name]['min_price'], total_price)
                    ota_summary[ota_name]['max_price'] = max(ota_summary[ota_name]['max_price'], total_price)
            
            # Calculate averages
            for ota_name, data in ota_summary.items():
                if data['count'] > 0:
                    prices = [offer.get('total_price') for offer in data['offers'] if offer.get('total_price') and isinstance(offer.get('total_price'), (int, float))]
                    if prices:
                        data['avg_price'] = sum(prices) / len(prices)
                    else:
                        data['avg_price'] = 0
            
            return ota_summary
            
        except Exception as e:
            print(f"Error creating OTA summary: {e}")
            return {}
    
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
        # Save JSON results
        json_file = f"tripadvisor_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(pricing_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nJSON results saved to: {json_file}")
        
        # Export OTA offers to CSV
        csv_file = scraper.export_to_csv(pricing_data)
        
        # Create and display OTA summary
        ota_summary = scraper.create_ota_summary(pricing_data)
        
        # Display summary
        print(f"\nSession-Based Scraping Summary:")
        print(f"Hotel ID: {pricing_data.get('hotel_id', 'Unknown')}")
        print(f"OTA offers found: {len(pricing_data.get('ota_offers', []))}")
        
        if ota_summary:
            print(f"\nOTA Summary (sorted by agency):")
            print("-" * 60)
            
            # Sort OTAs by name for consistent display
            for ota_name in sorted(ota_summary.keys()):
                data = ota_summary[ota_name]
                print(f"\n🏨 {ota_name}:")
                print(f"   Offers: {data['count']}")
                if data['min_price'] != float('inf'):
                    print(f"   Price Range: ${data['min_price']:.2f} - ${data['max_price']:.2f}")
                    print(f"   Average Price: ${data['avg_price']:.2f}")
                
                # Show individual offers for this OTA
                for i, offer in enumerate(data['offers'][:3]):  # Show first 3 offers
                    print(f"   Offer {i+1}:")
                    print(f"     Hotel: {offer.get('hotel_name', 'N/A')}")
                    print(f"     Location Code (G): {offer.get('location_code', 'N/A')}")
                    print(f"     Hotel ID (D): {offer.get('hotel_id', 'N/A')}")
                    print(f"     Total: ${offer.get('total_price', 'N/A')} {offer.get('currency', '')}")
                    print(f"     Base: ${offer.get('base_price', 'N/A')}")
                    print(f"     Tax: ${offer.get('tax', 'N/A')}")
                    print(f"     Occupants: {offer.get('occupants', 'N/A')} (Adults: {offer.get('adults', 'N/A')}, Children: {offer.get('children', 'N/A')})")
                    print(f"     Rooms: {offer.get('rooms', 'N/A')}")
                    print(f"     Check-in: {offer.get('check_in_date', 'N/A')}")
                    print(f"     Check-out: {offer.get('check_out_date', 'N/A')}")
                
                if len(data['offers']) > 3:
                    print(f"   ... and {len(data['offers']) - 3} more offers")
        
        if csv_file:
            print(f"\n📊 CSV Export:")
            print(f"   File: {csv_file}")
            print(f"   Columns: OTA_Name, Hotel_Name, Location_Code_G, Hotel_ID_D, Currency, Base_Price, Tax, Total_Price, Price_Per_Night, Check_In_Date, Check_Out_Date, Adults, Children, Occupants, Rooms, Extracted_At")
            print(f"   Ready for Excel/Google Sheets import!")
        
    else:
        print("\nSession-based scraping failed. Check the error messages above.")


if __name__ == "__main__":
    main()
