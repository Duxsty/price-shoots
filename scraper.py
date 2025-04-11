import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}


SCRAPINGBEE_API_KEY = "ABC123456789xyz"  # replace with your actual key

def get_price(url):
    print(f"[DEBUG] Starting scrape for URL: {url}")

    if "currys.co.uk" in url:
        return scrape_currys_price(url)

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"[DEBUG] HTTP Status: {response.status_code}")
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
            print(f"[DEBUG] Price text found: {price_text}")
            return float(price_text)

        print("[DEBUG] No matching price element found.")
    except Exception as e:
        print(f"[ERROR scraping site] {e}")

    return None


def scrape_currys_price(url):
    print(f"[DEBUG] Using ScrapingBee for Currys: {url}")
    api_url = 'https://app.scrapingbee.com/api/v1/'
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'true'
    }

    try:
        response = requests.get(api_url, params=params, timeout=15)
        print(f"[DEBUG] ScrapingBee response: {response.status_code}")
        soup = BeautifulSoup(response.text, 'html.parser')

        price_tag = soup.find('p', class_='product-price_price')
        if price_tag:
            price_text = price_tag.get_text().replace("£", "").replace(",", "").strip()
            print(f"[DEBUG] Currys price found: {price_text}")
            return float(price_text)

        # fallback
        fallback = soup.find("span", string=lambda s: s and "£" in s)
        if fallback:
            price_text = fallback.get_text().replace("£", "").replace(",", "").strip()
            print(f"[DEBUG] Currys fallback price found: {price_text}")
            return float(price_text)

        print("[DEBUG] No price found in Currys fallback.")
    except Exception as e:
        print(f"[ERROR scraping Currys] {e}")

    return None
