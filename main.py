from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Literal, List
from datetime import datetime
import uuid
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# === In-memory store ===
tracked_items = {}

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

# === Track a product ===
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

# === Get tracked products ===
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

# === Delete a tracked product ===
@app.delete("/delete-product/{product_id}")
async def delete_product(product_id: str):
    if product_id in tracked_items:
        del tracked_items[product_id]
        return {"message": "Product deleted successfully."}
    raise HTTPException(status_code=404, detail="Product not found")

# === Price search endpoint ===
SCRAPER_API_KEY = "your-real-key-here"
SCRAPER_API_URL = "https://api.scraperapi.com/"

@app.get("/search-prices", response_model=List[ProductResult])
async def search_prices(q: str = Query(..., description="Product name")):
    def fetch_currys():
        search_url = f"https://www.currys.co.uk/search?q={q}"
        payload = {
            "api_key": SCRAPER_API_KEY,
            "url": search_url
        }
        r = requests.get(SCRAPER_API_URL, params=payload)

        # TEMP: Debug output
        print("=== CURRYS RAW HTML SAMPLE ===")
        print(r.text[:3000])  # print first 3000 characters only

        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        for item in soup.select('[data-testid="product-tile"]'):
            name_el = item.select_one('[data-testid="product-title"]')
            price_el = item.select_one('[data-testid="product-price"]')
            link_el = item.select_one('a')

            if name_el and price_el and link_el:
                results.append({
                    "product_name": name_el.get_text(strip=True),
                    "price": float(
                        price_el.get_text(strip=True)
                            .replace("£", "")
                            .replace(",", "")
                            .split()[0]
                    ),
                    "source": "Currys",
                    "link": "https://www.currys.co.uk" + link_el["href"]
                })
        return results

    return fetch_currys()
