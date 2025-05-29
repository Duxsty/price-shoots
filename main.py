# main.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

# ← Set this in your Render (or other host) as an ENV var, do NOT hard-code in production
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "983bef082c2a1f0f051204994c7b2e47")
SCRAPER_API_URL = "http://api.scraperapi.com"

PRICE_SPY_SEARCH = "https://www.pricespy.co.uk/search?search={query}"
PRICE_SPY_DETAIL = "https://www.pricespy.co.uk/product/{id}"

class Product(BaseModel):
    id: str
    name: str
    imageUrl: str
    price: float
    store: Optional[str]
    rating: Optional[float]
    detailUrl: str

def _fetch_html(url: str) -> str:
    resp = httpx.get(
        SCRAPER_API_URL,
        params={
            "api_key": SCRAPER_API_KEY,
            "url": url,
            "premium": "true",
        },
        timeout=30.0
    )
    if resp.status_code != 200:
        raise HTTPException(502, f"ScraperAPI returned {resp.status_code}")
    return resp.text

@app.get("/search-prices", response_model=List[Product])
async def search_prices(q: str):
    html = _fetch_html(PRICE_SPY_SEARCH.format(query=httpx.utils.quote(q)))
    soup = BeautifulSoup(html, "html.parser")

    results: List[Product] = []
    for card in soup.select("div.productListing"):
        a = card.select_one("a.details-link")
        href = a["href"] if a and a.has_attr("href") else ""
        prod_id = href.split("/")[-1]

        name = a.text.strip() if a else "Unknown"
        img_el = card.select_one("img")
        img = img_el["data-src"] if img_el and img_el.has_attr("data-src") else ""
        price_el = card.select_one(".priceBlock .price")
        price = float(price_el.text.replace("£", "").replace(",", "")) if price_el else 0.0
        store_el = card.select_one(".retailerLogo img")
        store = store_el["alt"] if store_el and store_el.has_attr("alt") else None
        rating_el = card.select_one(".star-rating")
        rating = float(rating_el["data-rating"]) if rating_el and rating_el.has_attr("data-rating") else None

        results.append(
            Product(
                id=prod_id,
                name=name,
                imageUrl=img,
                price=price,
                store=store,
                rating=rating,
                detailUrl=f"https://www.pricespy.co.uk{href}",
            )
        )

    return results

@app.get("/product-detail/{prod_id}", response_model=Product)
async def product_detail(prod_id: str):
    html = _fetch_html(PRICE_SPY_DETAIL.format(id=prod_id))
    soup = BeautifulSoup(html, "html.parser")

    # Adjust selectors to match the real detail page structure
    name_el = soup.select_one("h1")
    name = name_el.text.strip() if name_el else "Unknown"

    img_el = soup.select_one(".primary-image img")
    img = img_el["src"] if img_el and img_el.has_attr("src") else ""

    price_el = soup.select_one(".priceBlock .price")
    price = float(price_el.text.replace("£", "").replace(",", "")) if price_el else 0.0

    rating_el = soup.select_one(".star-rating")
    rating = float(rating_el["data-rating"]) if rating_el and rating_el.has_attr("data-rating") else None

    # There’s no “store” on the detail page; leave null or parse if available
    return Product(
        id=prod_id,
        name=name,
        imageUrl=img,
        price=price,
        store=None,
        rating=rating,
        detailUrl=PRICE_SPY_DETAIL.format(id=prod_id),
    )
