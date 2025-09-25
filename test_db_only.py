#!/usr/bin/env python3
"""
Test only the database insertion with a known price
"""
import requests
import json

# Test data with the working hotel ID and a fake price for DB testing
test_data = {
    "geo_id": "g155032",
    "hotel_id": "d14134983",  # Hotel Birks Montreal
    "checkin_date": "2025-09-26",
    "checkout_date": "2025-09-28"
}

print("Testing database insertion with known working hotel...")
print(f"Request data: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(
        "http://127.0.0.1:8000/scrape-price/",
        json=test_data,
        timeout=30  # Shorter timeout for quicker feedback
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✅ SUCCESS: Database insertion worked!")
    elif response.status_code == 500 and "database" in response.text.lower():
        print("❌ DATABASE ERROR: Still having database issues")
    else:
        print(f"❌ OTHER ERROR: {response.status_code}")

except requests.exceptions.Timeout:
    print("⏰ TIMEOUT: Request took too long (probably still scraping)")
except requests.exceptions.RequestException as e:
    print(f"❌ REQUEST ERROR: {e}")