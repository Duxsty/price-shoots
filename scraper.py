import requests
from bs4 import BeautifulSoup
import re

SCRAPINGBEE_API_KEY = 'ABC123456789xyz'  # Replace with your real key

def scrape_currys_price(url):
    api_url = 'https://app.scrapingbee.com/api/v1/'
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'true'
    }

    try:
        response = requests.get(api_url, params=params, timeout=15)

        if response.status_code != 200:
            print("[ScrapingBee ERROR]", response.status_code, response.text)
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Try exact class (this might change frequently)
        price_tag = soup.find('p', class_='product-price_price')
        if price_tag:
            return float(price_tag.text.replace('£', '').replace(',', '').strip())

        # 2. Try regex fallback
        price_text = re.search(r'£\s?(\d+(?:,\d{3})*(?:\.\d{2})?)', soup.text)
        if price_text:
            return float(price_text.group(1).replace(',', ''))

        print("[Scraper WARNING] No price matched in HTML.")
        # Optional: save HTML for inspection
        # with open("debug_currys.html", "w", encoding="utf-8") as f:
        #     f.write(response.text)

    except Exception as e:
        print(f"[Scraper ERROR]: {e}")

    return None
