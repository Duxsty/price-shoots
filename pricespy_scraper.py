import requests
from bs4 import BeautifulSoup

def search_pricespy(query: str):
    results = []
    search_url = f"https://www.pricespy.co.uk/search?search={query.replace(' ', '+')}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(search_url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception(f"PriceSpy returned status code {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select("a[data-test='product-link']")

    for item in items[:5]:  # limit results
        try:
            name = item.get_text(strip=True)
            link = "https://www.pricespy.co.uk" + item["href"]
            results.append({
                "product_name": name,
                "price": None,
                "source": "PriceSpy",
                "link": link,
                "image": ""  # Optional: add logic to scrape image
            })
        except Exception:
            continue

    return results
