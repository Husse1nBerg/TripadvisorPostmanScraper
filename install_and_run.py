#!/usr/bin/env python3
"""
Installation and Quick Start Script for TripAdvisor Scraper

This script helps users install dependencies and run the scraper easily.
"""

import subprocess
import sys
import os


def install_requirements():
    """Install required packages."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def check_chrome():
    """Check if Chrome browser is installed."""
    print("Checking for Chrome browser...")
    
    # Check common Chrome installation paths
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome browser found!")
            return True
    
    # Try to find Chrome using system commands
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['where', 'chrome'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                print("✅ Chrome browser found via system PATH!")
                return True
        else:  # Unix-like systems
            result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                print("✅ Chrome browser found via system PATH!")
                return True
            
            result = subprocess.run(['which', 'chromium-browser'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                print("✅ Chromium browser found via system PATH!")
                return True
    except Exception:
        pass
    
    print("⚠️  Chrome browser not found in common locations.")
    print("Please install Chrome from: https://www.google.com/chrome/")
    print("Or try running the scraper anyway - webdriver-manager might find it automatically.")
    return False


def run_scraper():
    """Run the recommended scraper."""
    print("\n" + "="*50)
    print("Starting TripAdvisor Scraper")
    print("="*50)
    
    try:
        # Import and run the auto scraper
        from tripadvisor_selenium_auto import main
        main()
    except ImportError as e:
        print(f"❌ Error importing scraper: {e}")
        print("Make sure all dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        return False
    
    return True


def main():
    """Main installation and setup function."""
    print("TripAdvisor Scraper - Installation & Setup")
    print("="*40)
    
    # Step 1: Install requirements
    if not install_requirements():
        print("Installation failed. Please check your Python environment.")
        return
    
    # Step 2: Check Chrome
    chrome_ok = check_chrome()
    
    # Step 3: Ask user if they want to run the scraper
    run_now = input("\nWould you like to run the scraper now? (y/n): ").strip().lower()
    if run_now == 'y':
        if not chrome_ok:
            print("\n⚠️  Chrome not detected, but trying anyway...")
            print("webdriver-manager will attempt to find Chrome automatically.")
        run_scraper()
    else:
        print("\nYou can run the scraper later with:")
        print("python tripadvisor_selenium_auto.py")


if __name__ == "__main__":
    main()
