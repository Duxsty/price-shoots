# main.py

import os
import requests
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List
from bs4 import BeautifulSoup

app = FastAPI()

class Product(BaseModel):
    id: str
    name: str
    imageUrl: str = ""
    price: float

@app.get("/search-prices", response_model=List[Product])
def search_prices(q: str = Query(...)):
    # 1) Build the target PriceSpy URL
    target = f"https://www.pricespy.co.uk/search?search={requests.utils.quote(q)}"
    # 2) Build the ScraperAPI URL
    key = os.getenv("SCRAPERAPI_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="Missing SCRAPERAPI_KEY")
    sapar_url = f"http://api.scraperapi.com?api_key={key}&url={target}"

    # 3) Fetch via ScraperAPI
    resp = requests.get(sapar_url, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="ScraperAPI error")

    # 4) Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(".search-result")  # adjust selector to match PriceSpy's markup

    products = []
    for idx, c in enumerate(cards[:10]):  # limit to first 10 results
        title_el = c.select_one(".product-name a")
        price_el = c.select_one(".product-price .price")  # adjust as needed
        img_el = c.select_one(".product-image img")

        if not title_el or not price_el:
            continue

        name = title_el.get_text(strip=True)
        price_text = price_el.get_text().replace("£", "").replace(",", "")
        try:
            price = float(price_text)
        except:
            price = 0.0

        products.append(Product(
            id=str(idx),
            name=name,
            imageUrl=img_el["src"] if img_el and img_el.has_attr("src") else "",
            price=price
        ))

    return products
