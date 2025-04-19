from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pricespy_scraper import search_pricespy

app = FastAPI(title="PriceShoots API", version="1.0.0")

# Allow frontend access (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "PriceShoots API is up!"}

@app.get("/search-prices")
def search_prices(q: str = Query(...)):
    try:
        results = search_pricespy(q)
        if not results:
            raise HTTPException(status_code=404, detail="No results found")
        return results
    except Exception as e:
        print(f"Error during scraping: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
