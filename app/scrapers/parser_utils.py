import re
from typing import Optional
from bs4 import BeautifulSoup

def parse_tripadvisor_price(html_content: str) -> Optional[str]:
    """
    Parses the HTML content of a Tripadvisor page to find the price.
    Uses multiple strategies to locate price information reliably.

    Args:
        html_content: The raw HTML of the page.

    Returns:
        A cleaned price string (e.g., "529.00"), or None if not found.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Strategy 1: Look for price in common TripAdvisor selectors
        price_selectors = [
            '[data-automation="hotel-price"]',
            '[data-testid="price-summary"]',
            '.price',
            '.priceFrom',
            '[data-automation="price"]',
            '.offer-price',
            '.rate-price',
            '.starting-price',
            '[class*="price"]',
            '[class*="rate"]'
        ]

        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                if price_text and '$' in price_text:
                    # Extract price using regex
                    price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_text)
                    if price_match:
                        # Remove commas from price
                        return price_match.group(1).replace(',', '')

        # Strategy 2: Search for price patterns in all text
        price_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $123.45 or $1,234.56
            r'CAD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # CAD 123.45
            r'C\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'  # C$123.45
        ]

        all_text = soup.get_text()
        for pattern in price_patterns:
            matches = re.findall(pattern, all_text)
            if matches:
                # Return the first reasonable price (filter out very small amounts)
                for match in matches:
                    price_value = float(match.replace(',', ''))
                    if price_value >= 50:  # Reasonable minimum hotel price
                        return match.replace(',', '')

        # Strategy 3: Look for JSON-LD structured data
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Look for price in offers
                    if 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, list) and offers:
                            offer = offers[0]
                        else:
                            offer = offers

                        if isinstance(offer, dict) and 'price' in offer:
                            price = str(offer['price'])
                            # Clean the price
                            price_match = re.search(r'(\d+(?:\.\d{2})?)', price)
                            if price_match:
                                return price_match.group(1)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        return None

    except Exception as e:
        # Log the error but don't crash
        import logging
        logging.warning(f"Error parsing price: {e}")
        return None