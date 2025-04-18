from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

router = APIRouter()

class ProductResult(BaseModel):
    product_name: str
    price: float
    source: str
    link: str
    image: str = ""

@router.get("/search-prices", response_model=List[ProductResult])
def search_prices(query: str):
    encoded_query = quote(query)
    url = f"https://www.pricespy.co.uk/search?search={encoded_query}"
    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Pricespy results")

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select("div.product-card")  # adjust this based on HTML
    results = []

    for item in items:
        title_el = item.select_one(".product-card__heading")
        price_el = item.select_one(".product-card__price")
        link_el = item.select_one("a")
        image_el = item.select_one("img")

        if title_el and price_el and link_el:
            try:
                price = float(''.join(filter(str.isdigit, price_el.text))) / 100
                results.append(ProductResult(
                    product_name=title_el.text.strip(),
                    price=price,
                    source="PriceSpy",
                    link="https://www.pricespy.co.uk" + link_el.get("href", ""),
                    image=image_el.get("src", "") if image_el else ""
                ))
            except:
                continue

    return results
