import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-GB,en;q=0.9"
}

def get_price(url):
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
        # fallback for generic sites
        price = soup.find("span", string=lambda s: s and "£" in s)

    if price:
        try:
            price_text = price.get_text().replace("£", "").replace(",", "").strip()
            return float(price_text)
        except:
            return None
    return None
