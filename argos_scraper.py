# argos_scraper.py

import os
import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List

router = APIRouter()

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
SCRAPER_API_URL = "http://api.scraperapi.com"

class ProductResult(BaseModel):
    product_name: str
    price: str
    source: str
    link: str
    image: str

@router.get("/search-argos", response_model=List[ProductResult])
def search_argos(q: str = Query(..., description="Product name to search for")):
    if not SCRAPER_API_KEY:
        raise HTTPException(status_code=500, detail="ScraperAPI key not configured")

    try:
        target_url = f"https://www.argos.co.uk/search/{q.replace(' ', '%20')}/"
        response = requests.get(SCRAPER_API_URL, params={"api_key": SCRAPER_API_KEY, "url": target_url})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("ul[data-test='component-product-card'] li")

        results = []
        for item in items:
            title_tag = item.select_one("a[data-test='component-product-card-title']")
            price_tag = item.select_one("div[data-test='component-product-card-price']")
            image_tag = item.select_one("img")

            if not title_tag or not price_tag:
                continue

            product_name = title_tag.get_text(strip=True)
            link = "https://www.argos.co.uk" + title_tag.get("href", "")
            price = price_tag.get_text(strip=True)
            image = image_tag["src"] if image_tag else ""

            results.append(ProductResult(
                product_name=product_name,
                price=price,
                source="Argos",
                link=link,
                image=image
            ))

        if not results:
            raise HTTPException(status_code=404, detail="No products found")

        return results

    except Exception as e:
        print(f"❌ Argos scraper error: {e}")
        raise HTTPException(status_code=500, detail="Failed to scrape Argos")
