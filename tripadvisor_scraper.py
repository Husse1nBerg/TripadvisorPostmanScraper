#!/usr/bin/env python3
"""
TripAdvisor Hotel Price Scraper

Automates scraping hotel prices from TripAdvisor by replicating the Postman request.
"""

import re
import json
import requests
from datetime import datetime, timedelta


class TripAdvisorScraper:
    def __init__(self):
        self.base_url = "https://www.tripadvisor.com/data/graphql/ids"
        self.headers = {
            "X-Tripadvisor-Api-Key": "trip-service-HAC-2021",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Origin": "https://www.tripadvisor.com"
        }

    def parse_tripadvisor_url(self, url):
        """
        Parse TripAdvisor URL to extract hotel ID and location ID.
        Returns (hotel_id, location_id) or (None, None) if parsing fails.
        """
        try:
            # Flexible regex: matches '-d' followed by digits
            hotel_id_match = re.search(r'-d(\d+)', url)
            if not hotel_id_match:
                print(f"Error: Could not extract hotel ID from URL: {url}")
                return None, None

            hotel_id = int(hotel_id_match.group(1))
            location_id = hotel_id  # usually same for TripAdvisor

            print(f"Successfully parsed URL:")
            print(f"  Hotel ID: {hotel_id}")
            print(f"  Location ID: {location_id}")

            return hotel_id, location_id

        except Exception as e:
            print(f"Error parsing URL: {e}")
            return None, None

    def build_request_payload(self, hotel_id, location_id, check_in_date=None, check_out_date=None, adults=2, rooms=1):
        """Build the GraphQL request payload."""
        # Default to tomorrow and day after if dates not provided
        if not check_in_date:
            check_in_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if not check_out_date:
            check_out_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        payload = [
            {
                "variables": {
                    "request": {
                        "hotelId": hotel_id,
                        "trackingEnabled": True,
                        "requestCaller": "Hotel_Review",
                        "impressionPlacement": "HR_DirectCommerce",
                        "currencyCode": "USD",
                        "travelInfo": {
                            "adults": adults,
                            "rooms": rooms,
                            "checkInDate": check_in_date,
                            "checkOutDate": check_out_date,
                            "childAgesPerRoom": []
                        }
                    },
                    "locationId": location_id
                },
                "extensions": {
                    "preRegisteredQueryId": "1ad9fb68f3f0cdaf"
                }
            }
        ]
        return payload

    def make_request(self, payload):
        """Make the POST request to TripAdvisor GraphQL endpoint."""
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response.text}")
            return None

    def parse_pricing_data(self, response_data):
        """
        Parse pricing data from TripAdvisor response.
        Returns structured dictionary or None if response is empty.
        """
        if not response_data:
            return None

        try:
            # This will depend on actual response; here we keep raw JSON for now
            pricing_info = {
                "raw_response": response_data,
                "extracted_at": datetime.now().isoformat()
            }
            return pricing_info
        except Exception as e:
            print(f"Error parsing response data: {e}")
            return None

    def scrape_hotel_prices(self, url, check_in_date=None, check_out_date=None, adults=2, rooms=1):
        """Main method to scrape hotel prices from TripAdvisor."""
        print(f"Starting price scraping for URL: {url}")
        print("=" * 60)

        hotel_id, location_id = self.parse_tripadvisor_url(url)
        if not hotel_id or not location_id:
            return None

        payload = self.build_request_payload(
            hotel_id, location_id, check_in_date, check_out_date, adults, rooms
        )

        response_data = self.make_request(payload)
        if not response_data:
            return None

        pricing_data = self.parse_pricing_data(response_data)

        print("=" * 60)
        print("Scraping completed!")

        return pricing_data


def main():
    scraper = TripAdvisorScraper()

    print("TripAdvisor Hotel Price Scraper")
    print("=" * 40)

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

    pricing_data = scraper.scrape_hotel_prices(url, check_in, check_out, adults, rooms)

    if pricing_data:
        output_file = f"tripadvisor_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pricing_data, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    else:
        print("\nScraping failed. Please check the URL and try again.")


if __name__ == "__main__":
    main()
