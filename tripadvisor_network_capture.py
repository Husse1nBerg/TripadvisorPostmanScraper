#!/usr/bin/env python3
"""
TripAdvisor Network Capture Scraper

This version captures the actual network requests made by the browser
to get the real session data, cookies, and payload structure.
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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
import requests


class TripAdvisorNetworkCapture:
    def __init__(self, headless=False):  # Default to visible for debugging
        self.headless = headless
        self.driver = None
        self.captured_requests = []
        
    def setup_driver_with_logging(self):
        """Setup Chrome WebDriver with network logging enabled."""
        try:
            print("Setting up Chrome WebDriver with network logging...")
            
            # Enable logging
            caps = DesiredCapabilities.CHROME
            caps['goog:loggingPrefs'] = {'performance': 'ALL'}
            
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Network logging options
            chrome_options.add_argument("--enable-logging")
            chrome_options.add_argument("--log-level=0")
            chrome_options.add_argument("--v=1")
            
            # Standard options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options, desired_capabilities=caps)
            
            print("Chrome WebDriver with network logging initialized")
            return True
            
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def capture_network_requests(self, url):
        """Capture network requests while navigating to the page."""
        try:
            print(f"Capturing network requests for: {url}")
            
            # Navigate to the page
            self.driver.get(url)
            time.sleep(10)  # Wait for all requests to complete
            
            # Get performance logs
            logs = self.driver.get_log('performance')
            print(f"Captured {len(logs)} performance log entries")
            
            # Filter for network requests
            network_requests = []
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    if 'tripadvisor.com' in response['url']:
                        network_requests.append({
                            'url': response['url'],
                            'status': response['status'],
                            'headers': response.get('headers', {}),
                            'timestamp': log['timestamp']
                        })
            
            print(f"Found {len(network_requests)} TripAdvisor network requests")
            
            # Look for GraphQL requests
            graphql_requests = [req for req in network_requests if 'graphql' in req['url']]
            print(f"Found {len(graphql_requests)} GraphQL requests")
            
            for req in graphql_requests:
                print(f"GraphQL request: {req['url']} (Status: {req['status']})")
            
            return network_requests
            
        except Exception as e:
            print(f"Error capturing network requests: {e}")
            return []
    
    def extract_cookies_from_browser(self):
        """Extract cookies from the browser."""
        try:
            cookies = {}
            selenium_cookies = self.driver.get_cookies()
            for cookie in selenium_cookies:
                cookies[cookie['name']] = cookie['value']
            
            print(f"Extracted {len(cookies)} cookies from browser")
            print(f"Cookie names: {list(cookies.keys())}")
            
            return cookies
            
        except Exception as e:
            print(f"Error extracting cookies: {e}")
            return {}
    
    def try_manual_request_with_captured_data(self, url, hotel_id):
        """Try to make a manual request using captured data."""
        try:
            print("Attempting manual request with captured data...")
            
            # Extract cookies
            cookies = self.extract_cookies_from_browser()
            
            # Build payload (using your discovered structure)
            payload = [
                {
                    "variables": {
                        "locationId": hotel_id,
                        "trafficSource": "ba",
                        "deviceType": "DESKTOP",
                        "servletName": "Hotel_Review",
                        "hotelTravelInfo": {
                            "adultCount": 2,
                            "checkInDate": "2025-09-27",
                            "checkOutDate": "2025-09-28",
                            "childrenCount": 0,
                            "childAgesPerRoom": "",
                            "roomCount": 1,
                            "usedDefaultDates": False
                        },
                        "withContactLinks": False
                    },
                    "extensions": {
                        "preRegisteredQueryId": "d9072109f7378ce1"
                    }
                },
                {
                    "variables": {
                        "request": {
                            "hotelId": hotel_id,
                            "trackingEnabled": True,
                            "requestCaller": "Hotel_Review",
                            "impressionPlacement": "HR_DirectCommerce",
                            "pageLoadUid": str(uuid.uuid4()),
                            "sessionId": "D2855F001712C827E756B613E9303C14",
                            "currencyCode": "USD",
                            "requestNumber": 0,
                            "spAttributionToken": None,
                            "shapeStrategy": "DEFAULT_DESKTOP_OFFER_SHAPE",
                            "sequenceId": 0,
                            "travelInfo": {
                                "adults": 2,
                                "rooms": 1,
                                "checkInDate": "2025-09-27",
                                "checkOutDate": "2025-09-28",
                                "childAgesPerRoom": [],
                                "usedDefaultDates": False
                            }
                        },
                        "locationId": hotel_id
                    },
                    "extensions": {
                        "preRegisteredQueryId": "1ad9fb68f3f0cdaf"
                    }
                }
            ]
            
            # Make request
            headers = {
                "X-Tripadvisor-Api-Key": "trip-service-HAC-2021",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Origin": "https://www.tripadvisor.com",
                "Referer": url,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            response = requests.post(
                "https://www.tripadvisor.com/data/graphql/ids",
                headers=headers,
                json=payload,
                cookies=cookies,
                timeout=30
            )
            
            print(f"Manual request status: {response.status_code}")
            print(f"Response content length: {len(response.content)}")
            
            if response.status_code == 200 and response.content:
                try:
                    data = response.json()
                    print("✅ Manual request successful!")
                    return data
                except json.JSONDecodeError:
                    print("Response is not valid JSON")
                    print(f"Raw response: {response.text[:500]}...")
            else:
                print(f"Manual request failed: {response.status_code}")
                print(f"Response: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"Error in manual request: {e}")
            return None
    
    def run_network_capture(self, url):
        """Run the full network capture process."""
        print("TripAdvisor Network Capture Scraper")
        print("=" * 45)
        
        # Parse hotel ID
        hotel_id_match = re.search(r'-d(\d+)', url)
        if not hotel_id_match:
            print("Error: Could not extract hotel ID from URL")
            return None
        
        hotel_id = int(hotel_id_match.group(1))
        print(f"Hotel ID: {hotel_id}")
        
        # Setup WebDriver
        if not self.setup_driver_with_logging():
            return None
        
        try:
            # Capture network requests
            network_requests = self.capture_network_requests(url)
            
            # Try manual request with captured data
            result = self.try_manual_request_with_captured_data(url, hotel_id)
            
            return {
                "hotel_id": hotel_id,
                "url": url,
                "network_requests": network_requests,
                "api_result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error during network capture: {e}")
            return None
        
        finally:
            self.close_driver()


def main():
    """Main function to run network capture."""
    print("TripAdvisor Network Capture Scraper")
    print("=" * 40)
    print("This will capture actual network requests to understand the API calls.")
    print()
    
    capture = TripAdvisorNetworkCapture(headless=False)  # Use visible browser for debugging
    
    # Get URL from user
    url = input("Enter TripAdvisor hotel URL: ").strip()
    if not url:
        print("Error: No URL provided")
        return
    
    # Run network capture
    result = capture.run_network_capture(url)
    
    if result:
        # Save results
        output_file = f"tripadvisor_network_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Display summary
        print(f"\nNetwork Capture Summary:")
        print(f"Hotel ID: {result['hotel_id']}")
        print(f"Network requests captured: {len(result['network_requests'])}")
        print(f"API request successful: {'Yes' if result['api_result'] else 'No'}")
        
        if result['api_result']:
            print("✅ Successfully captured and replicated API calls!")
        else:
            print("❌ API replication failed - check the network requests for clues")
    else:
        print("Network capture failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
