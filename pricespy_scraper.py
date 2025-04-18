
from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel
from playwright.async_api import async_playwright

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
            await page.wait_for_selector("a[data-test='product-link']", timeout=15000)
        except Exception as e:
            print(f"⚠️ Wait timeout: {e}")
            await browser.close()
            return []

        items = await page.query_selector_all("a[data-test='product-link']")

        for item in items:
            try:
                name = await item.inner_text()
                href = await item.get_attribute("href")
                full_url = f"https://www.pricespy.co.uk{href}"
                results.append(PriceSpyResult(
                    product_name=name.strip(),
                    price=0.0,  # Placeholder
                    source="PriceSpy",
                    link=full_url,
                    image=""
                ))
            except Exception as e:
                print(f"❌ Parsing error: {e}")
                continue

        await browser.close()
    return results

@router.get("/search-pricespy", response_model=List[PriceSpyResult])
async def search_pricespy(q: str = Query(...)):
    try:
        data = await scrape_pricespy(q)
        if not data:
            raise HTTPException(status_code=404, detail="No results found")
        return data
    except Exception as e:
        print(f"❌ Exception in /search-pricespy: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
