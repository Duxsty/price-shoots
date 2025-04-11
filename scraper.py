import requests
from bs4 import BeautifulSoup

# User-Agent headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-GB,en;q=0.9"
}

# Set your actual ScrapingBee API key here
SCRAPINGBEE_API_KEY = 'ABC123456789xyz'

def get_price(url):
    """Main entry point to get product price from URL."""
    try:
        if "currys.co.uk" in url:
            return scrape_currys_price(url)

        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        if "amazon." in url:
            price = (
                soup.select_one("#priceblock_dealprice") or
                soup.select_one("#priceblock_ourprice") or
                soup.select_one("span.a-price span.a-offscreen")
            )

        elif "ebay." in url:
            price = (
                soup.select_one(".x-price-approx__value") or
                soup.select_one(".notranslate")
            )

        else:
            # Generic fallback: find any span containing a pound sign
            price = soup.find("span", string=lambda s: s and "£" in s)

        if price:
            return clean_price(price.get_text())
    except Exception as e:
        print(f"[ERROR] Failed to get price from {url}: {e}")

    return None

def scrape_currys_price(url):
    """Scrape price from Currys using ScrapingBee with JS rendering."""
    api_url = 'https://app.scrapingbee.com/api/v1/'
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'true'
    }

    try:
        response = requests.get(api_url, params=params, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check the HTML to confirm correct class
        price = soup.find('p', class_='product-price_price')

        # Optional fallback using visible pound-text
        if not price:
            price = soup.find(string=lambda s: s and "£" in s)

        if price:
            return clean_price(price)
    except Exception as e:
        print(f"[ERROR] Currys scrape failed: {e}")

    return None

def clean_price(text):
    """Extract and return a float from a price string like '£849.99'."""
    try:
        cleaned = text.replace("£", "").replace(",", "").strip()
        return float(cleaned)
    except ValueError:
        print(f"[ERROR] Failed to convert '{text}' to float")
        return None
