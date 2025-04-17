from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Literal, List
from datetime import datetime
import uuid
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load secrets from .env file if running locally
load_dotenv()

app = FastAPI()

# === In-memory store ===
tracked_items = {}

# === Config ===
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
SERPAPI_URL = "https://serpapi.com/search.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

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

class SummaryResult(BaseModel):
    summary: str

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
@app.get("/search-prices", response_model=List[ProductResult])
async def search_prices(q: str = Query(..., description="Product name")):
    try:
        params = {
            "engine": "google_shopping",
            "q": q,
            "gl": "uk",
            "hl": "en",
            "api_key": SERPAPI_KEY
        }
        res = requests.get(SERPAPI_URL, params=params, timeout=20)
        res.raise_for_status()
        data = res.json()
        results = []

        for item in data.get("shopping_results", []):
            title = item.get("title")
            price_str = item.get("price", "0").replace("\u00a3", "").replace(",", "")
            link = item.get("link")
            source = item.get("source", "Unknown")

            try:
                price = float(price_str.split()[0])
                results.append({
                    "product_name": title,
                    "price": price,
                    "source": source,
                    "link": link
                })
            except Exception as parse_err:
                print(f"Error parsing price: {parse_err}")

        if not results:
            raise Exception("No results matched parsing rules.")

        return results

    except Exception as e:
        print("ERROR in search_prices():", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch or parse prices.")

# === GPT Product Summary ===
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
