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
async def search_prices(q: str = Query(...)):
    def scrape(site_name, url, parser_func):
        try:
            res = requests.get(SCRAPER_API_URL, params={"api_key": SCRAPER_API_KEY, "url": url}, timeout=25)
            res.raise_for_status()
            return parser_func(res.text)
        except Exception as e:
            print(f"Error scraping {site_name}: {e}")
            return []

    def parse_currys(html):
        soup = BeautifulSoup(html, "html.parser")
        products = []
        for item in soup.select('[data-testid="product-tile"]'):
            title = item.select_one('[data-testid="product-title"]')
            price_el = item.select_one('[data-testid="product-price"]')
            link = item.find('a', href=True)
            if title and price_el and link:
                try:
                    price = float(price_el.text.strip().replace("£", "").split()[0])
                    products.append({
                        "product_name": title.text.strip(),
                        "price": price,
                        "source": "Currys",
                        "link": "https://www.currys.co.uk" + link['href']
                    })
                except:
                    continue
        return products

    def parse_amazon(html):
        soup = BeautifulSoup(html, "html.parser")
        products = []
        for item in soup.select(".s-result-item"):
            title = item.select_one("h2")
            price_whole = item.select_one(".a-price-whole")
            price_frac = item.select_one(".a-price-fraction")
            link = item.select_one("a.a-link-normal", href=True)
            if title and price_whole and link:
                try:
                    price = float(f"{price_whole.text.strip()}.{price_frac.text.strip() if price_frac else '00'}")
                    products.append({
                        "product_name": title.text.strip(),
                        "price": price,
                        "source": "Amazon",
                        "link": "https://www.amazon.co.uk" + link["href"]
                    })
                except:
                    continue
        return products

    def parse_argos(html):
        soup = BeautifulSoup(html, "html.parser")
        products = []
        for item in soup.select(".ProductCardstyles__Title-sc-1fgptbz-11"):
            title = item.text.strip()
            parent = item.find_parent("a", href=True)
            price_el = parent.find_next("div", class_="ProductCardstyles__PriceLabel-sc-1fgptbz-16")
            if price_el and parent:
                try:
                    price = float(price_el.text.strip().replace("£", "").split()[0])
                    products.append({
                        "product_name": title,
                        "price": price,
                        "source": "Argos",
                        "link": "https://www.argos.co.uk" + parent['href']
                    })
                except:
                    continue
        return products

    def parse_johnlewis(html):
        soup = BeautifulSoup(html, "html.parser")
        products = []
        for item in soup.select("li.product-card"):
            title = item.select_one(".product-card__title")
            price_el = item.select_one(".product-price")
            link = item.select_one("a", href=True)
            if title and price_el and link:
                try:
                    price = float(price_el.text.strip().replace("£", "").split()[0])
                    products.append({
                        "product_name": title.text.strip(),
                        "price": price,
                        "source": "John Lewis",
                        "link": "https://www.johnlewis.com" + link['href']
                    })
                except:
                    continue
        return products

    results = []
    results += scrape("Currys", f"https://www.currys.co.uk/search?q={q}", parse_currys)
    results += scrape("Amazon", f"https://www.amazon.co.uk/s?k={q}", parse_amazon)
    results += scrape("Argos", f"https://www.argos.co.uk/search/{q}", parse_argos)
    results += scrape("John Lewis", f"https://www.johnlewis.com/search?q={q}", parse_johnlewis)

    if not results:
        raise HTTPException(status_code=500, detail="Failed to fetch or parse prices.")
    return results
