import re
from typing import Optional
from bs4 import BeautifulSoup

# The selector is owned by the parser, where it belongs.
PRICE_SELECTOR = "[data-automation='metaPrice']"

def parse_tripadvisor_price(html_content: str) -> Optional[str]:
    """
    Parses the HTML content of a Tripadvisor page to find the price.

    Args:
        html_content: The raw HTML of the page.

    Returns:
        A cleaned price string (e.g., "529.00"), or None if not found.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        price_element = soup.select_one(PRICE_SELECTOR)

        if not price_element:
            return None

        price_text = price_element.get_text(strip=True)
        # Use regex to extract only digits and a potential decimal point
        cleaned_price = re.sub(r'[^\d.]', '', price_text)
        
        return cleaned_price if cleaned_price else None
    except Exception:
        # If any parsing error occurs, return None
        return None