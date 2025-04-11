import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def get_price(url: str):
    print(f"🌐 Fetching URL: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📡 Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"⚠️ Non-200 response: {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        # Try different selectors
        selectors = [
            {"name": "Amazon", "pattern": "span.a-price-whole"},
            {"name": "Currys", "pattern": "div[class*=ProductPriceBlock]"},
            {"name": "Generic Price", "pattern": "[class*=price]"},
        ]

        for sel in selectors:
            print(f"🔎 Trying selector: {sel['pattern']} for {sel['name']}")
            element = soup.select_one(sel["pattern"])
            if element:
                text = element.get_text(strip=True)
                print(f"✅ Found price text: {text}")
                price = extract_price(text)
                if price is not None:
                    print(f"💰 Extracted price: {price}")
                    return price
                else:
                    print(f"❌ Could not extract price from: {text}")

        print("❌ No valid price element found.")
        return None

    except Exception as e:
        print(f"💥 Exception during scraping: {str(e)}")
        return None

def extract_price(text: str):
    # Remove currency symbols, commas, etc.
    cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
    try:
        return float(cleaned)
    except ValueError:
        print(f"❌ Failed to convert price: {text}")
        return None
