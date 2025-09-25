#!/usr/bin/env python3
"""
TripAdvisor Alternative Scraper

Alternative approaches when stealth methods fail:
1. Use different user agents and browser configurations
2. Try different entry points
3. Use residential proxy rotation
4. Manual browser automation with human intervention
"""

import re
import json
import time
import random
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TripAdvisorAlternative:
    def __init__(self):
        self.session = requests.Session()
        
    def try_direct_api_approach(self, hotel_id):
        """Try to find alternative API endpoints or data sources."""
        print("Trying alternative API approaches...")
        
        # Common alternative endpoints that might work
        endpoints = [
            f"https://www.tripadvisor.com/api/v1/hotels/{hotel_id}",
            f"https://www.tripadvisor.com/restaurants/{hotel_id}",
            f"https://www.tripadvisor.com/Attraction_Review-g{hotel_id}",
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tripadvisor.com/',
        }
        
        for endpoint in endpoints:
            try:
                print(f"Trying endpoint: {endpoint}")
                response = self.session.get(endpoint, headers=headers, timeout=10)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✅ Found data at {endpoint}")
                        return data
                    except:
                        print(f"Response is not JSON at {endpoint}")
                else:
                    print(f"❌ Failed at {endpoint}")
                    
            except Exception as e:
                print(f"Error with {endpoint}: {e}")
        
        return None
    
    def try_mobile_version(self, url):
        """Try accessing the mobile version of the site."""
        print("Trying mobile version...")
        
        mobile_url = url.replace("www.tripadvisor.com", "m.tripadvisor.com")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            }
            
            response = self.session.get(mobile_url, headers=headers, timeout=15)
            print(f"Mobile version status: {response.status_code}")
            
            if response.status_code == 200:
                # Look for prices in the mobile HTML
                content = response.text
                price_patterns = [
                    r'\$[\d,]+(?:\.\d{2})?',
                    r'CAD\s*[\d,]+(?:\.\d{2})?',
                    r'USD\s*[\d,]+(?:\.\d{2})?'
                ]
                
                prices = []
                for pattern in price_patterns:
                    matches = re.findall(pattern, content)
                    prices.extend(matches)
                
                if prices:
                    print(f"✅ Found {len(prices)} prices in mobile version")
                    return {
                        "source": "mobile_version",
                        "prices": list(set(prices)),
                        "url": mobile_url
                    }
            
        except Exception as e:
            print(f"Error accessing mobile version: {e}")
        
        return None
    
    def try_different_browsers(self, url):
        """Try different browser configurations."""
        print("Trying different browser configurations...")
        
        browser_configs = [
            {
                "name": "Firefox User Agent",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
            },
            {
                "name": "Safari User Agent", 
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
            },
            {
                "name": "Edge User Agent",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            }
        ]
        
        for config in browser_configs:
            try:
                print(f"Trying {config['name']}...")
                
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument(f"--user-agent={config['user_agent']}")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Execute stealth scripts
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                driver.get(url)
                time.sleep(5)
                
                # Check if blocked
                page_source = driver.page_source.lower()
                if "unusual activity" not in page_source and "bot activity" not in page_source:
                    print(f"✅ {config['name']} worked!")
                    
                    # Look for prices
                    currency_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$') or contains(text(), 'CAD') or contains(text(), 'USD')]")
                    if currency_elements:
                        prices = []
                        for elem in currency_elements:
                            text = elem.text.strip()
                            if text and len(text) < 100:
                                prices.append(text)
                        
                        driver.quit()
                        return {
                            "source": config['name'],
                            "prices": prices,
                            "success": True
                        }
                
                driver.quit()
                print(f"❌ {config['name']} still blocked")
                
            except Exception as e:
                print(f"Error with {config['name']}: {e}")
        
        return None
    
    def manual_approach_instructions(self, url):
        """Provide instructions for manual scraping."""
        print("\n" + "="*60)
        print("MANUAL APPROACH INSTRUCTIONS")
        print("="*60)
        print("Since automated scraping is being blocked, here are manual alternatives:")
        print()
        print("1. MANUAL BROWSER AUTOMATION:")
        print("   - Open Chrome manually")
        print("   - Navigate to the hotel page")
        print("   - Use browser developer tools (F12)")
        print("   - Look for network requests to find API endpoints")
        print("   - Copy the request headers and payload")
        print()
        print("2. USE DIFFERENT NETWORK:")
        print("   - Try from a different IP address")
        print("   - Use a VPN service")
        print("   - Try from a different device/network")
        print()
        print("3. ALTERNATIVE DATA SOURCES:")
        print("   - Booking.com API")
        print("   - Expedia API")
        print("   - Hotels.com API")
        print("   - Google Hotels")
        print()
        print("4. BROWSER EXTENSION:")
        print("   - Create a browser extension that runs in the user's browser")
        print("   - This bypasses bot detection since it runs in a real browser")
        print()
        print("5. PROXY ROTATION:")
        print("   - Use residential proxy services")
        print("   - Rotate IP addresses for each request")
        print("   - Use different user agents")
        print()
        print("6. CAPTCHA SOLVING:")
        print("   - Use services like 2captcha or Anti-Captcha")
        print("   - Solve captchas automatically")
        print()
        return {
            "manual_instructions": True,
            "url": url,
            "alternatives": [
                "Manual browser automation",
                "Different network/VPN",
                "Alternative data sources",
                "Browser extension",
                "Proxy rotation",
                "Captcha solving"
            ]
        }
    
    def run_alternatives(self, url, hotel_id):
        """Run all alternative approaches."""
        print("TripAdvisor Alternative Scraper")
        print("=" * 40)
        print("Trying multiple alternative approaches...")
        print()
        
        results = []
        
        # Try 1: Direct API approach
        api_result = self.try_direct_api_approach(hotel_id)
        if api_result:
            results.append({"method": "direct_api", "data": api_result})
        
        # Try 2: Mobile version
        mobile_result = self.try_mobile_version(url)
        if mobile_result:
            results.append({"method": "mobile_version", "data": mobile_result})
        
        # Try 3: Different browsers
        browser_result = self.try_different_browsers(url)
        if browser_result:
            results.append({"method": "different_browsers", "data": browser_result})
        
        # If all automated methods fail, provide manual instructions
        if not results:
            manual_result = self.manual_approach_instructions(url)
            results.append({"method": "manual_instructions", "data": manual_result})
        
        return results


def main():
    """Main function to run alternative approaches."""
    print("TripAdvisor Alternative Scraper")
    print("=" * 40)
    print("This will try multiple alternative approaches to get hotel prices.")
    print()
    
    alternative = TripAdvisorAlternative()
    
    # Get URL from user
    url = input("Enter TripAdvisor hotel URL: ").strip()
    if not url:
        print("Error: No URL provided")
        return
    
    # Extract hotel ID
    hotel_id_match = re.search(r'-d(\d+)', url)
    if not hotel_id_match:
        print("Error: Could not extract hotel ID from URL")
        return
    
    hotel_id = hotel_id_match.group(1)
    print(f"Hotel ID: {hotel_id}")
    print()
    
    # Run alternative approaches
    results = alternative.run_alternatives(url, hotel_id)
    
    # Save results
    output_file = f"tripadvisor_alternatives_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Display summary
    print(f"\nAlternative Approaches Summary:")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['method']}: {'✅ Success' if result['data'] else '❌ Failed'}")
        if result['data'] and 'prices' in result['data']:
            print(f"   Prices found: {len(result['data']['prices'])}")
    
    if not any(result['data'] for result in results if result['method'] != 'manual_instructions'):
        print("\n❌ All automated approaches failed.")
        print("Consider using the manual approaches listed in the results file.")


if __name__ == "__main__":
    main()

