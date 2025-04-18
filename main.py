from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import quote
import requests
import os

app = FastAPI()

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

class ProductResult(BaseModel):
    product_name: str
    price: float
    source: str
    link: str
    image: str = ""
    rating: float | None = None

def scrape_currys(query: str) -> List[ProductResult]:
    encoded = quote(query)
    url = f"https://www.currys.co.uk/search?q={encoded}"
    api_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
    if res.status_code != 200:
        print(f"Currys error: {res.status_code}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    items = []
    products = soup.select("div.productListItem")  # Updated selector

    print(f"🛒 Currys: Found {len(products)} product entries")

    for product in products:
        name = product.select_one("h2.productTitle")
        price_el = product.select_one("strong[data-testid='product-price']")
        link_el = product.select_one("a")
        image_el = product.select_one("img")

        if name and price_el and link_el:
            price_text = ''.join(filter(str.isdigit, price_el.get_text()))
            price = float(price_text[:-2]) if len(price_text) > 2 else 0
            items.append(ProductResult(
                product_name=name.get_text(strip=True),
                price=price,
                link="https://www.currys.co.uk" + link_el["href"],
                source="Currys",
                image=image_el["src"] if image_el and image_el.has_attr("src") else "",
                rating=None
            ))
    return items



def scrape_argos(query: str) -> List[ProductResult]:
    encoded = quote(query)
    url = f"https://www.argos.co.uk/search/{encoded}/"
    api_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
    if res.status_code != 200:
        print(f"Argos error: {res.status_code}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    items = []
    products = soup.select("li[data-test='component-product-card']")

    print(f"🛍️ Argos: Found {len(products)} product entries")

    for product in products:
        try:
            name_el = product.select_one("h2 span[data-test='product-title']")
            price_el = product.select_one("strong[data-test='product-price']")
            link_el = product.select_one("a[data-test='component-product-card-title']")
            image_el = product.select_one("img")

            if name_el and price_el and link_el:
                raw_price = ''.join(filter(str.isdigit, price_el.get_text()))
                price = float(raw_price[:-2]) if len(raw_price) > 2 else 0

                items.append(ProductResult(
                    product_name=name_el.get_text(strip=True),
                    price=price,
                    link="https://www.argos.co.uk" + link_el["href"],
                    source="Argos",
                    image=image_el["src"] if image_el and image_el.has_attr("src") else "",
                    rating=None
                ))
        except Exception as e:
            print(f"❌ Failed to parse Argos product: {e}")
            continue

    return items

@app.get("/search-prices", response_model=List[ProductResult])
async def search_prices(q: str = Query(...)):
    try:
        currys = scrape_currys(q)
        argos = scrape_argos(q)
        combined = currys + argos
        if not combined:
            raise HTTPException(status_code=404, detail="No products found")
        return combined
    except Exception as e:
        print(f"❌ Exception during search: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch or parse prices.")
