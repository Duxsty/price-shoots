from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

SCRAPER_API_KEY = os.getenv("SCRAPERAPI_KEY")  # set this in Render env vars

app = FastAPI()

class ProductResult(BaseModel):
    product_name: str
    price: str
    source: str
    link: str

@app.get("/")
def root():
    return {"message": "PriceShoots API is running."}

@app.get("/search-prices", response_model=List[ProductResult])
def search_prices(q: str = Query(...)):
    if not SCRAPER_API_KEY:
        raise HTTPException(status_code=500, detail="Missing ScraperAPI key")

    encoded_query = quote_plus(q)
    target_url = f"https://www.currys.co.uk/search?q={encoded_query}"
    scraper_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={target_url}"

    try:
        response = requests.get(scraper_url, timeout=20)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="ScraperAPI failed")

        soup = BeautifulSoup(response.text, "html.parser")
        product_cards = soup.select("[data-testid='product-tile']")

        results = []
        for card in product_cards[:5]:  # limit results to first 5
            name = card.select_one("[data-testid='product-title']")
            price = card.select_one("[data-testid='product-price']")
            link = card.find("a", href=True)

            if name and price and link:
                results.append(ProductResult(
                    product_name=name.get_text(strip=True),
                    price=price.get_text(strip=True),
                    source="Currys",
                    link=f"https://www.currys.co.uk{link['href']}"
                ))

        if not results:
            raise HTTPException(status_code=404, detail="No results found")

        return results

    except Exception as e:
        print(f"Scrape error: {e}")
        raise HTTPException(status_code=500, detail="Scraping failed")
