
import asyncio
from playwright.async_api import async_playwright
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

class PriceSpyResult(BaseModel):
    product_name: str
    price: float
    source: str
    link: str
    image: str

async def scrape_pricespy(query: str) -> List[PriceSpyResult]:
    results = []
    url = f"https://www.pricespy.co.uk/search?search={query.replace(' ', '+')}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        try:
            await page.wait_for_selector(".SearchResults__grid___3oKZp", timeout=15000)
        except:
            await browser.close()
            return []

        products = await page.query_selector_all("div[data-test='product-card']")

        for product in products:
            try:
                title_el = await product.query_selector("a[data-test='product-link']")
                price_el = await product.query_selector("[data-test='product-price']")
                image_el = await product.query_selector("img")

                name = await title_el.inner_text() if title_el else "Unnamed"
                price_raw = await price_el.inner_text() if price_el else "£0"
                price = float(''.join(filter(str.isdigit, price_raw))) / 100 if price_raw else 0.0
                link = "https://www.pricespy.co.uk" + await title_el.get_attribute("href") if title_el else ""
                image = await image_el.get_attribute("src") if image_el else ""

                results.append(PriceSpyResult(
                    product_name=name.strip(),
                    price=price,
                    source="PriceSpy",
                    link=link,
                    image=image
                ))
            except Exception as e:
                print(f"Error parsing product: {e}")
                continue

        await browser.close()
    return results

@router.get("/search-pricespy", response_model=List[PriceSpyResult])
async def search_pricespy(q: str = Query(...)):
    try:
        data = await scrape_pricespy(q)
        if not data:
            raise HTTPException(status_code=404, detail="No PriceSpy results found")
        return data
    except Exception as e:
        print(f"❌ Exception in /search-pricespy: {e}")
        raise HTTPException(status_code=500, detail="Search failed")
