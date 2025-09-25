#!/usr/bin/env python3
"""
Test Chrome WebDriver Setup

This script tests if Chrome and ChromeDriver are working properly.
"""

import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def test_chrome_setup():
    """Test if Chrome WebDriver can be initialized."""
    print("Testing Chrome WebDriver setup...")
    print("=" * 40)
    
    driver = None
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        print("1. Downloading/Setting up ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        print("2. Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("3. Testing navigation...")
        driver.get("https://www.google.com")
        
        title = driver.title
        print(f"4. Page title: {title}")
        
        if "Google" in title:
            print("✅ SUCCESS: Chrome WebDriver is working properly!")
            return True
        else:
            print("⚠️  WARNING: Chrome loaded but unexpected page title")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure Chrome browser is installed")
        print("2. Check your internet connection (needed to download ChromeDriver)")
        print("3. Try running as administrator (Windows)")
        print("4. Check if antivirus is blocking the download")
        return False
        
    finally:
        if driver:
            driver.quit()
            print("5. WebDriver closed successfully")


def main():
    """Main test function."""
    print("Chrome WebDriver Test")
    print("=" * 20)
    
    success = test_chrome_setup()
    
    if success:
        print("\n🎉 Great! You can now run the TripAdvisor scraper:")
        print("python tripadvisor_selenium_auto.py")
    else:
        print("\n🔧 Please fix the issues above before running the scraper.")
        print("\nAlternative solutions:")
        print("1. Install Chrome from: https://www.google.com/chrome/")
        print("2. Try running the scraper anyway - it might work:")
        print("   python tripadvisor_selenium_auto.py")
        print("3. Use the manual Selenium version:")
        print("   python tripadvisor_selenium_scraper.py")


if __name__ == "__main__":
    main()

