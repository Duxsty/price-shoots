from fastapi import FastAPI, HTTPException, Query
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is running."}

@app.get("/search-prices")
def search_prices(q: str = Query(..., min_length=1)):
    try:
        search_url = f"https://www.pricespy.co.uk/search?search={q.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="PriceSpy is unreachable.")

        soup = BeautifulSoup(response.text, "html.parser")
        product_links = soup.select("a[data-test='product-link']")

        if not product_links:
            raise HTTPException(status_code=404, detail="No results found")

        # Return top 3 products with name and link
        results = []
        for a in product_links[:3]:
            name = a.get_text(strip=True)
            href = a.get("href")
            results.append({
                "name": name,
                "link": f"https://www.pricespy.co.uk{href}"
            })

        return results

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
