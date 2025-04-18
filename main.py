
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import quote
import requests
import os

app = FastAPI()

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

class ProductResult(BaseModel):
    product_name: str
    price: float
    source: str
    link: str
    image: str = ""
    rating: float | None = None

@app.get("/search-prices", response_model=List[ProductResult])
async def search_prices(q: str = Query(...)):
    encoded_query = quote(q)
    target_url = f"https://www.currys.co.uk/search?q={encoded_query}"
    api_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"

    try:
        res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch from ScraperAPI")

        soup = BeautifulSoup(res.text, "html.parser")
        items = []

        for product in soup.select("li.product"):
            name = product.select_one("h2.product-title")
            price_el = product.select_one(".product-price")
            link_el = product.select_one("a")
            image_el = product.select_one("img")

            if name and price_el and link_el:
                raw_price = ''.join(filter(str.isdigit, price_el.get_text()))
                price = float(raw_price[:-2]) if len(raw_price) >= 3 else 0

                items.append({
                    "product_name": name.get_text(strip=True),
                    "price": price,
                    "link": f"https://www.currys.co.uk{link_el['href']}",
                    "source": "Currys",
                    "image": image_el['src'] if image_el and image_el.has_attr('src') else "",
                    "rating": None
                })

        if not items:
            raise HTTPException(status_code=404, detail="No products found")

        return items

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch or parse prices.")
