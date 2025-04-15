from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Literal, List
from datetime import datetime
import uuid
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# In-memory store
tracked_items = {}

# ScraperAPI setup
SCRAPER_API_KEY = "63d85fc08b759603903edc1d015458b0"
SCRAPER_API_URL = "https://api.scraperapi.com/"

# === Models ===

class TrackRequest(BaseModel):
    product_name: str
    target_price: float
    email: EmailStr
    check_frequency: Literal["daily", "every_2_days", "weekly"]
    end_date: datetime

class ProductResult(BaseModel):
    product_name: str
    price: float
    source: str
    link: str

# === Track endpoints ===

@app.post("/track-product")
async def track_product(req: TrackRequest):
    item_id = str(uuid.uuid4())
    tracked_items[item_id] = {
        "product_name": req.product_name,
        "target_price": req.target_price,
        "email": req.email,
        "check_frequency": req.check_frequency,
        "end_date": req.end_date.isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    return {"id": item_id, "message": "Tracking started successfully."}

@app.get("/tracked-products")
async def get_tracked_products(email: EmailStr = Query(...)):
    results = [
        {"id": item_id, **item}
        for item_id, item in tracked_items.items()
        if item["email"] == email
    ]
    if not results:
        raise HTTPException(status_code=404, detail="No tracked products found.")
    return results

@app.delete("/delete-product/{product_id}")
async def delete_product(product_id: str):
    if product_id in tracked_items:
        del tracked_items[product_id]
        return {"message": "Product deleted successfully."}
    raise HTTPException(status_code=404, detail="Product not found")

# === Price search endpoint ===

@app.get("/search-prices", response_model=List[ProductResult])
async def search_prices(q: str = Query(..., description="Product name")):
    def fetch_currys():
        search_url = f"https://www.currys.co.uk/search?q={q}"
        payload = {
            "api_key": SCRAPER_API_KEY,
            "url": search_url
        }
        r = requests.get(SCRAPER_API_URL, params=payload)
        soup = BeautifulSoup(r.text, "html.parser")

        results = []
        for item in soup.select(".ProductCard"):
            name_el = item.select_one(".ProductCard-title")
            price_el = item.select_one(".ProductCard-price")
            link_el = item.select_one("a.ProductCard-link")

            if not all([name_el, price_el, link_el]):
                continue

            name = name_el.get_text(strip=True)
            price_text = price_el.get_text(strip=True).replace("£", "").replace(",", "")
            try:
                price = float(price_text)
            except ValueError:
                continue

            link = "https://www.currys.co.uk" + link_el["href"]
            results.append({
                "product_name": name,
                "price": price,
                "source": "Currys",
                "link": link
            })

        return results

    return fetch_currys()
