#!/usr/bin/env python3
"""
Test script for the TripAdvisor scraper API
"""
import requests
import json
from datetime import date, timedelta

# API endpoint
API_BASE = "http://127.0.0.1:8000"

def test_scraper():
    # Test with proper TripAdvisor IDs (example values)
    test_data = {
        "geo_id": "g155032",  # Montreal geo ID example
        "hotel_id": "d15704640",  # Example hotel ID
        "checkin_date": (date.today() + timedelta(days=3)).isoformat(),
        "checkout_date": (date.today() + timedelta(days=5)).isoformat()
    }

    print(f"Testing with data: {json.dumps(test_data, indent=2)}")
    print(f"Making request to: {API_BASE}/scrape-price/")

    try:
        response = requests.post(
            f"{API_BASE}/scrape-price/",
            json=test_data,
            timeout=180
        )

        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")

        if response.status_code == 200:
            print("✅ SUCCESS: Price scraping worked!")
        else:
            print(f"❌ FAILED: Status code {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")

def test_invalid_ids():
    """Test the validation for invalid IDs"""
    test_data = {
        "geo_id": "string",  # This should trigger validation error
        "hotel_id": "string",
        "checkin_date": (date.today() + timedelta(days=3)).isoformat(),
        "checkout_date": (date.today() + timedelta(days=5)).isoformat()
    }

    print(f"\nTesting validation with invalid IDs: {json.dumps(test_data, indent=2)}")

    try:
        response = requests.post(
            f"{API_BASE}/scrape-price/",
            json=test_data,
            timeout=30
        )

        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")

        if response.status_code == 400:
            print("✅ SUCCESS: Validation correctly rejected invalid IDs!")
        else:
            print(f"❌ VALIDATION FAILED: Expected 400, got {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")

if __name__ == "__main__":
    print("🧪 Testing TripAdvisor Scraper API")
    print("=" * 50)

    # Test validation first
    test_invalid_ids()

    # Test actual scraping
    test_scraper()