#!/usr/bin/env python3
"""
TripAdvisor Diagnostic Scraper

This version focuses on diagnosing why prices aren't being found.
It will show us exactly what's on the page and help identify the issue.
"""

import re
import json
import time
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


class TripAdvisorDiagnostic:
    def __init__(self, headless=False):  # Default to visible for debugging
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with minimal restrictions."""
        try:
            print("Setting up diagnostic Chrome WebDriver...")
            
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
            
            # Automatically download and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            print("Diagnostic Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def take_screenshot(self, filename):
        """Take a screenshot for debugging."""
        try:
            screenshot_path = os.path.join(os.getcwd(), filename)
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"Could not take screenshot: {e}")
            return None
    
    def analyze_page_content(self):
        """Analyze the page content to understand what we're seeing."""
        try:
            print("\n" + "="*60)
            print("PAGE CONTENT ANALYSIS")
            print("="*60)
            
            # Get basic page info
            print(f"Current URL: {self.driver.current_url}")
            print(f"Page Title: {self.driver.title}")
            print(f"Page Source Length: {len(self.driver.page_source)} characters")
            
            # Check if we're on the right page
            if "hotel" not in self.driver.title.lower() and "tripadvisor" not in self.driver.title.lower():
                print("⚠️  WARNING: Page title doesn't contain 'hotel' or 'tripadvisor'")
                print("This might indicate we're on a different page than expected")
            
            # Look for common TripAdvisor elements
            print("\nLooking for TripAdvisor-specific elements...")
            
            # Check for hotel name elements
            hotel_elements = self.driver.find_elements(By.XPATH, "//h1")
            print(f"Found {len(hotel_elements)} h1 elements:")
            for i, elem in enumerate(hotel_elements[:5]):  # Show first 5
                print(f"  {i+1}. {elem.text[:100]}...")
            
            # Check for any elements containing price-like text
            print("\nLooking for elements containing currency symbols...")
            currency_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '$') or contains(text(), '€') or contains(text(), '£') or contains(text(), 'CAD') or contains(text(), 'USD')]")
            print(f"Found {len(currency_elements)} elements with currency symbols:")
            for i, elem in enumerate(currency_elements[:10]):  # Show first 10
                text = elem.text.strip()
                if text and len(text) < 200:  # Avoid very long text
                    print(f"  {i+1}. {text}")
            
            # Check for common price-related classes
            print("\nLooking for price-related CSS classes...")
            price_classes = [
                "price", "rate", "amount", "cost", "booking", "provider",
                "listing", "hotel", "room", "night", "per", "total"
            ]
            
            for class_name in price_classes:
                elements = self.driver.find_elements(By.CSS_SELECTOR, f"[class*='{class_name}']")
                if elements:
                    print(f"  Found {len(elements)} elements with class containing '{class_name}'")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.text.strip()
                        if text and len(text) < 100:
                            print(f"    {i+1}. {text}")
            
            # Check for any buttons or clickable elements
            print("\nLooking for clickable elements...")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            links = self.driver.find_elements(By.TAG_NAME, "a")
            print(f"Found {len(buttons)} buttons and {len(links)} links")
            
            # Look for elements with data-testid attributes
            print("\nLooking for elements with data-testid attributes...")
            testid_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid]")
            print(f"Found {len(testid_elements)} elements with data-testid:")
            for i, elem in enumerate(testid_elements[:10]):  # Show first 10
                testid = elem.get_attribute("data-testid")
                text = elem.text.strip()
                if text and len(text) < 100:
                    print(f"  {i+1}. data-testid='{testid}' -> {text}")
            
            # Check if there are any error messages or blocked content
            print("\nLooking for error messages or blocked content...")
            error_indicators = [
                "blocked", "error", "not available", "access denied", "forbidden",
                "captcha", "robot", "bot", "automated", "suspicious"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in error_indicators:
                if indicator in page_text:
                    print(f"  ⚠️  Found potential issue: '{indicator}' in page content")
            
            # Save page source for manual inspection
            with open("page_source_diagnostic.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("\nPage source saved to: page_source_diagnostic.html")
            
            return True
            
        except Exception as e:
            print(f"Error analyzing page content: {e}")
            return False
    
    def try_different_interactions(self):
        """Try different ways to interact with the page."""
        try:
            print("\n" + "="*60)
            print("TRYING DIFFERENT INTERACTIONS")
            print("="*60)
            
            # Wait a bit
            time.sleep(3)
            
            # Try scrolling
            print("1. Scrolling to bottom...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.take_screenshot("03_after_scroll_bottom.png")
            
            # Scroll back to top
            print("2. Scrolling to top...")
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Try clicking on various elements
            print("3. Looking for clickable price elements...")
            clickable_selectors = [
                "button", "a", "[role='button']", "[onclick]", "[data-testid*='price']",
                "[class*='price']", "[class*='rate']", "[class*='booking']"
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements[:5]:  # Try first 5 elements
                        if elem.is_displayed() and elem.is_enabled():
                            text = elem.text.strip()
                            if text and any(word in text.lower() for word in ['price', 'rate', 'book', 'view', 'show']):
                                print(f"  Clicking: {text[:50]}...")
                                try:
                                    self.driver.execute_script("arguments[0].click();", elem)
                                    time.sleep(2)
                                except Exception as e:
                                    print(f"    Click failed: {e}")
                except Exception:
                    continue
            
            # Take final screenshot
            self.take_screenshot("04_after_interactions.png")
            
            return True
            
        except Exception as e:
            print(f"Error during interactions: {e}")
            return False
    
    def run_diagnostic(self, url):
        """Run the full diagnostic process."""
        print("TripAdvisor Diagnostic Tool")
        print("="*40)
        
        # Setup WebDriver
        if not self.setup_driver():
            return None
        
        try:
            # Navigate to page
            print(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            # Take initial screenshot
            self.take_screenshot("01_initial_page.png")
            
            # Analyze page content
            self.analyze_page_content()
            
            # Try interactions
            self.try_different_interactions()
            
            # Final analysis
            print("\n" + "="*60)
            print("FINAL ANALYSIS")
            print("="*60)
            
            # Look for prices one more time after interactions
            currency_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '$') or contains(text(), '€') or contains(text(), '£') or contains(text(), 'CAD') or contains(text(), 'USD')]")
            print(f"After interactions, found {len(currency_elements)} elements with currency symbols")
            
            if currency_elements:
                print("Currency elements found:")
                for i, elem in enumerate(currency_elements[:5]):
                    text = elem.text.strip()
                    if text and len(text) < 200:
                        print(f"  {i+1}. {text}")
            else:
                print("❌ No currency elements found - this explains why no prices were detected")
            
            # Check if we need to handle cookies or age verification
            if "cookie" in self.driver.page_source.lower() or "age" in self.driver.page_source.lower():
                print("⚠️  Page might have cookie consent or age verification")
            
            print("\nDiagnostic complete! Check the screenshots and page_source_diagnostic.html for details.")
            
            return {
                "url": url,
                "title": self.driver.title,
                "currency_elements_found": len(currency_elements),
                "screenshots_taken": ["01_initial_page.png", "03_after_scroll_bottom.png", "04_after_interactions.png"],
                "page_source_saved": "page_source_diagnostic.html"
            }
            
        except Exception as e:
            print(f"Error during diagnostic: {e}")
            return None
        
        finally:
            self.close_driver()


def main():
    """Main diagnostic function."""
    print("TripAdvisor Diagnostic Tool")
    print("This will help us understand why prices aren't being found.")
    print("="*60)
    
    # Ask user for preferences
    headless_input = input("Run in headless mode? (y/n) [default: n for debugging]: ").strip().lower()
    headless = headless_input == 'y'
    
    diagnostic = TripAdvisorDiagnostic(headless=headless)
    
    # Get URL from user
    url = input("Enter TripAdvisor hotel URL: ").strip()
    if not url:
        print("Error: No URL provided")
        return
    
    # Run diagnostic
    result = diagnostic.run_diagnostic(url)
    
    if result:
        print(f"\nDiagnostic Results:")
        print(f"URL: {result['url']}")
        print(f"Title: {result['title']}")
        print(f"Currency elements found: {result['currency_elements_found']}")
        print(f"Screenshots: {', '.join(result['screenshots_taken'])}")
        print(f"Page source: {result['page_source_saved']}")
        
        if result['currency_elements_found'] == 0:
            print("\n🔍 DIAGNOSIS: No currency elements found on the page.")
            print("Possible causes:")
            print("1. TripAdvisor is blocking automated browsers")
            print("2. Prices are loaded via JavaScript that we're not triggering")
            print("3. The page structure has changed significantly")
            print("4. We need to handle cookies/age verification first")
            print("\nCheck the screenshots to see what's actually on the page.")
    else:
        print("Diagnostic failed. Please check the error messages above.")


if __name__ == "__main__":
    main()

