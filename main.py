# main.py

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="PriceShoots API",
    description="Simplified backend for PriceShoots using PriceSpy redirect",
    version="1.0.0"
)

class Product(BaseModel):
    id: str
    name: str
    imageUrl: str = ""
    price: float

@app.get("/")
def root():
    return {"message": "API is running."}

@app.get("/search-prices", response_model=List[Product])
async def search_prices(q: str = Query(..., description="Search query")):
    # TODO: replace this stub with real scraping logic
    # For now we return two dummy products so the Flutter UI can display something
    return [
        Product(id="1", name=f"{q} Dummy Item", imageUrl="", price=9.99),
        Product(id="2", name=f"{q} Sample Item", imageUrl="", price=19.99),
    ]
