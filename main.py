import os
import asyncio
from fastapi import FastAPI
from pricespy_scraper import router as pricespy_router

# Force Playwright to install Chromium at runtime (for Render)
async def install_browser():
    os.system("playwright install chromium --with-deps")

# Run installation before the app starts
asyncio.run(install_browser())

app = FastAPI(
    title="PriceShoots API",
    description="Product price tracking using PriceSpy and other sources",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "API is running."}

# Register PriceSpy scraper routes
app.include_router(pricespy_router)
