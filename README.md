# TripAdvisor Hotel Price Scraper

This project provides multiple approaches to scrape hotel prices from TripAdvisor, including both API-based and browser automation methods.

##  Important Note

The original API-based approach (`tripadvisor_scraper.py`) may return 400 Bad Request errors due to TripAdvisor's anti-bot measures. **We recommend using the browser automation approach** (`tripadvisor_selenium_auto.py`) which is more reliable.

## Available Scripts

### 1. Browser Automation (Recommended)
- **File**: `tripadvisor_selenium_auto.py`
- **Method**: Uses Selenium with automatic ChromeDriver management
- **Pros**: Bypasses API restrictions, works with real browser sessions
- **Cons**: Requires Chrome browser, slower than API calls

### 2. Manual Selenium Setup
- **File**: `tripadvisor_selenium_scraper.py`
- **Method**: Uses Selenium with manual ChromeDriver setup
- **Pros**: More control over WebDriver configuration
- **Cons**: Requires manual ChromeDriver installation

### 3. API-Based (Legacy)
- **File**: `tripadvisor_scraper.py`
- **Method**: Direct GraphQL API calls
- **Pros**: Fast, lightweight
- **Cons**: May be blocked by TripAdvisor's anti-bot measures

## Features

- ✅ Automatically parses TripAdvisor hotel URLs to extract hotel ID
- ✅ Browser automation bypasses API restrictions
- ✅ Automatic ChromeDriver management (no manual setup required)
- ✅ Comprehensive price extraction from rendered HTML
- ✅ Extracts hotel information (name, rating)
- ✅ Finds booking providers and their prices
- ✅ Saves results to timestamped JSON files
- ✅ Configurable travel parameters (dates, adults, rooms)
- ✅ Headless mode option for server environments

## Installation

1. **Install Python 3.7 or higher**

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome browser** (required for Selenium scripts)
   - Download from: https://www.google.com/chrome/
   - The script will automatically manage ChromeDriver

## Usage

### Recommended: Browser Automation with Auto WebDriver Management

```bash
python tripadvisor_selenium_auto.py
```

### Manual Selenium Setup (if you prefer manual control)

```bash
python tripadvisor_selenium_scraper.py
```

### Legacy API Approach (may not work due to restrictions)

```bash
python tripadvisor_scraper.py
```

### Example URL Format
```
https://www.tripadvisor.ca/Hotel_Review-g155032-d14134983-Reviews-Hotel_Birks_Montreal-Montreal_Quebec.html
```

## How It Works

### Browser Automation Approach:
1. **Parse URL** to extract hotel ID (14134983)
2. **Launch Chrome browser** (headless or visible)
3. **Navigate** to the TripAdvisor hotel page
4. **Wait** for prices to load dynamically
5. **Extract** pricing data from rendered HTML
6. **Save** results to timestamped JSON file

### API Approach (Legacy):
1. Parse URL to extract hotel ID and location ID
2. Build GraphQL request payload
3. Make HTTP POST request to TripAdvisor's GraphQL endpoint
4. Parse and save response data

## Output

The scripts generate JSON files with the format:
```
tripadvisor_prices_auto_YYYYMMDD_HHMMSS.json
```

### Sample Output Structure:
```json
{
  "extracted_at": "2024-01-15T10:30:00",
  "url": "https://www.tripadvisor.ca/Hotel_Review-g155032-d14134983-Reviews-Hotel_Birks_Montreal-Montreal_Quebec.html",
  "hotel_id": 14134983,
  "scraping_method": "selenium_browser_automation_auto",
  "hotel_info": {
    "name": "Hotel Birks Montreal",
    "rating": "4.5"
  },
  "prices": [
    {
      "text": "$189 per night",
      "clean": "189",
      "selector": ".price"
    }
  ],
  "booking_providers": [
    {
      "text": "Booking.com - $189",
      "selector": ".booking-provider"
    }
  ]
}
```

## Configuration Options

- **Headless mode**: Run browser in background (default: enabled)
- **Travel dates**: Check-in/check-out dates (default: tomorrow/day after)
- **Guests**: Number of adults and rooms (default: 2 adults, 1 room)

## Troubleshooting

### Common Issues:

1. **ChromeDriver errors**: The auto script handles this automatically
2. **No prices found**: TripAdvisor may have changed their HTML structure
3. **Slow performance**: Browser automation is slower than API calls
4. **Blocked requests**: Use browser automation instead of API approach

### Solutions:

- Use `tripadvisor_selenium_auto.py` for best reliability
- Run in non-headless mode to see what's happening: `n` when prompted
- Check if Chrome browser is installed and up-to-date
- Try different hotel URLs to test functionality

## Technical Details

- **Selenium**: Web browser automation
- **ChromeDriver**: Automatic management via webdriver-manager
- **Price Extraction**: Multiple CSS selectors for robust data extraction
- **Error Handling**: Comprehensive exception handling and logging
- **Data Cleaning**: Removes duplicates and formats price data

## Disclaimer

This tool is for educational and research purposes only. Please:
- Respect TripAdvisor's terms of service
- Use reasonable request rates to avoid overloading their servers
- Consider the legal implications of web scraping in your jurisdiction
- Be mindful of robots.txt and rate limiting
