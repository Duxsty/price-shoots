import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-GB,en;q=0.9"
}

SCRAPINGBEE_API_KEY = 'ABC123456789xyz'  # Replace with your actual key

def get_price(url):
    if "currys.co.uk" in url:
        return scrape_currys_price(url)

    try:
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
            price = soup.find("span", string=lambda s: s and "£" in s)

        if price:
            price_text = price.get_text().replace("£", "").replace(",", "").strip()
            return float(price_text)
    except Exception as e:
        print(f"[ERROR scraping generic site] {e}")
        return None

    return None


def scrape_currys_price(url):
    api_url = 'https://app.scrapingbee.com/api/v1/'
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'true'
    }

    try:
        response = requests.get(api_url, params=params, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        price_tag = soup.find('p', class_='product-price_price')
        if price_tag:
            price_text = price_tag.get_text().replace("£", "").replace(",", "").strip()
            return float(price_text)

        # ⛑ fallback: try other similar selectors
        fallback = soup.find("span", string=lambda s: s and "£" in s)
        if fallback:
            price_text = fallback.get_text().replace("£", "").replace(",", "").strip()
            return float(price_text)

    except Exception as e:
        print(f"[ERROR scraping Currys] {e}")
        return None

    return None
