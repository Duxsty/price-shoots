
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
import requests
import os

app = FastAPI()

SERP_API_KEY = "29394e61566756e5badb6ae7b58ff789a1652ac4e2dbc03a5fda1d102a802a60"

class ProductResult(BaseModel):
    product_name: str
    price: float
    source: str
    link: str
    image: str = ""
    rating: float | None = None

@app.get("/search-prices", response_model=List[ProductResult])
async def search_prices(q: str = Query(...)):
    params = {
        "api_key": SERP_API_KEY,
        "engine": "amazon_uk",
        "amazon_domain": "amazon.co.uk",
        "type": "search",
        "search_term": q
    }
    res = requests.get("https://serpapi.com/search.json", params=params)

    if res.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch from SerpAPI")

    data = res.json()
    results = []

    for product in data.get("organic_results", []):
        try:
            results.append({
                "product_name": product.get("title", "Unnamed"),
                "price": float(product.get("price", {}).get("value", 0)),
                "source": "Amazon",
                "link": product.get("link", ""),
                "image": product.get("thumbnail", ""),
                "rating": float(product.get("rating", 0)) if product.get("rating") else None
            })
        except Exception as e:
            continue

    if not results:
        raise HTTPException(status_code=404, detail="No products found")

    return results
