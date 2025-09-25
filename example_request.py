#!/usr/bin/env python3
"""
Example API request with REAL TripAdvisor IDs
"""
import requests
import json
from datetime import date, timedelta

# Example: Fairmont The Queen Elizabeth in Montreal
# URL: https://www.tripadvisor.ca/Hotel_Review-g155032-d186688-Reviews-Fairmont_The_Queen_Elizabeth-Montreal_Quebec.html

test_data = {
    "geo_id": "g155032",      # Montreal geo ID
    "hotel_id": "d186688",    # Fairmont Queen Elizabeth hotel ID
    "checkin_date": "2025-09-26",
    "checkout_date": "2025-09-28"
}

print("Testing with REAL TripAdvisor IDs:")
print(json.dumps(test_data, indent=2))

response = requests.post(
    "http://127.0.0.1:8000/scrape-price/",
    json=test_data,
    timeout=180
)

print(f"\nStatus: {response.status_code}")
print(f"Response: {response.text}")