
import asyncio
from playwright.async_api import async_playwright
from typing import List
from pydantic import BaseModel

class ProductResult(BaseModel):
    product_name: str
    price: float
    link: str
    image: str
    source: str = "Argos"

async def scrape_argos_playwright(query: str) -> List[ProductResult]:
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        search_url = f"https://www.argos.co.uk/search/{query.replace(' ', '%20')}/"
        await page.goto(search_url, timeout=60000)

        await page.wait_for_selector("li[data-test='component-product-card']", timeout=15000)
        product_cards = await page.query_selector_all("li[data-test='component-product-card']")

        for card in product_cards:
            try:
                title_el = await card.query_selector("h2 span[data-test='product-title']")
                price_el = await card.query_selector("strong[data-test='product-price']")
                link_el = await card.query_selector("a[data-test='component-product-card-title']")
                image_el = await card.query_selector("img")

                title = await title_el.inner_text() if title_el else "Unnamed"
                price_raw = await price_el.inner_text() if price_el else "0"
                price = float(''.join(filter(str.isdigit, price_raw))) / 100 if price_raw else 0.0
                link = "https://www.argos.co.uk" + await link_el.get_attribute("href") if link_el else ""
                image = await image_el.get_attribute("src") if image_el else ""

                results.append(ProductResult(
                    product_name=title.strip(),
                    price=price,
                    link=link,
                    image=image
                ))
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue

        await browser.close()
    return results

# Example usage:
if __name__ == "__main__":
    query = "Lenovo IdeaPad 3 15.6in i5 8GB 256GB Laptop M365 Bundle"
    results = asyncio.run(scrape_argos_playwright(query))
    for r in results:
        print(r.model_dump())
