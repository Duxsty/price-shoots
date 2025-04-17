from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Literal, List
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# === TEMP: Return mock search results ===
@app.get("/search-prices", response_model=List[ProductResult])
async def search_prices(q: str = Query(..., description="Product name")):
    q_normalized = q.strip().lower()

    if "airpods" in q_normalized:
        return [
            {
                "product_name": "AirPods Pro (2nd Gen)",
                "price": 219.99,
                "source": "Amazon",
                "link": "https://www.amazon.co.uk/dp/B0BDJ8VQWL"
            },
            {
                "product_name": "AirPods Pro from Currys",
                "price": 229.00,
                "source": "Currys",
                "link": "https://www.currys.co.uk/products/apple-airpods-pro-2nd-gen"
            },
            {
                "product_name": "AirPods Pro (Refurbished)",
                "price": 189.99,
                "source": "Argos",
                "link": "https://www.argos.co.uk/product/12345678"
            }
        ]

    raise HTTPException(status_code=500, detail="Failed to fetch or parse prices.")

# === GPT Summary Endpoint (Optional) ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

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
        import requests
        r = requests.post(OPENAI_API_URL, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        data = r.json()
        summary = data["choices"][0]["message"]["content"]
        return {"summary": summary}
    except Exception as e:
        print("GPT Summary Error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to generate summary.")
