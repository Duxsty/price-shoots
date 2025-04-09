import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_amazon_price(url):
    if "amazon.co.uk" not in url:
        return None

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    price_tag = soup.find("span", {"class": "a-offscreen"})
    if price_tag:
        price_text = price_tag.get_text().replace("£", "").replace(",", "").strip()
        return float(price_text)
    
    return None