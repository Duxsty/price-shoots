from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Literal, List
from datetime import datetime
import uuid
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

tracked_items = {}

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
SCRAPER_API_URL = "https://api.scraperapi.com/"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

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

class SummaryResult(BaseModel):
    summary: str

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

@app.get("/search-prices", response_model=List[ProductResult])
async def search_prices(q: str = Query(..., description="Product name")):
    try:
        search_url = f"https://www.currys.co.uk/search?q={q}"
        payload = {"api_key": SCRAPER_API_KEY, "url": search_url}
        r = requests.get(SCRAPER_API_URL, params=payload, timeout=20)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        # Try multiple selectors for flexibility
        product_blocks = soup.select('[data-testid="product-tile"]')
        if not product_blocks:
            product_blocks = soup.select(".product, .product-card")

        for item in product_blocks:
            name_el = item.select_one('[data-testid="product-title"], h2, .product-title')
            price_el = item.select_one('[data-testid="product-price"], .product-price, span.price')
            link_el = item.find("a", href=True)

            if name_el and price_el and link_el:
                try:
                    price = float(
                        price_el.get_text(strip=True)
                            .replace("\u00a3", "")
                            .replace("£", "")
                            .replace(",", "")
                            .split()[0]
                    )
                    results.append({
                        "product_name": name_el.get_text(strip=True),
                        "price": price,
                        "source": "Currys",
                        "link": "https://www.currys.co.uk" + link_el.get("href", "")
                    })
                except Exception as e:
                    print(f"Price parse error: {e}")

        return results  # Return empty list if none found (no crash)

    except Exception as e:
        print("ERROR in fetch_currys():", str(e))
        return []

@app.get("/product-summary", response_model=SummaryResult)
async def product_summary(q: str = Query(..., description="Product name")):
    prompt = f"Write a short product description for: {q}\nKeep it simple and informative."
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful product assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        r = requests.post(OPENAI_API_URL, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        data = r.json()
        summary = data["choices"][0]["message"]["content"]
        return {"summary": summary}
    except Exception as e:
        print("GPT Summary Error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to generate summary.")
