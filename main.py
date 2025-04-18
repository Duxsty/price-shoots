from fastapi import FastAPI
from pricespy_scraper import router as pricespy_router

app = FastAPI(
    title="PriceShoots API",
    description="Product price tracking using PriceSpy and other sources",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "API is running."}

# Register PriceSpy router
app.include_router(pricespy_router)
