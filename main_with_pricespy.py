
from fastapi import FastAPI
from pricespy_scraper import router as pricespy_router

app = FastAPI()

# Register the PriceSpy search router
app.include_router(pricespy_router)

@app.get("/")
def root():
    return {"message": "Price Tracker API is running."}
