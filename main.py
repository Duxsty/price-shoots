import subprocess
from fastapi import FastAPI
from pricespy_scraper import router as pricespy_router

# One-time Playwright browser install (sync call)
def ensure_playwright_browser():
    try:
        subprocess.run(
            ["playwright", "install", "chromium"],
            check=True
        )
    except Exception as e:
        print(f"⚠️ Failed to install Playwright browser: {e}")

ensure_playwright_browser()

app = FastAPI(
    title="PriceShoots API",
    description="Product price tracking using PriceSpy and other sources",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "API is running."}

# Register routers
app.include_router(pricespy_router)
