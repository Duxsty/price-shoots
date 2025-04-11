from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from scraper import scrape_price

app = FastAPI()

class TrackRequest(BaseModel):
    url: str
    target_price: float

@app.post("/track-price")
def track_price(data: TrackRequest):
    price = scrape_price(data.url)
    if price is None:
        raise HTTPException(status_code=404, detail="Unable to retrieve price from the URL provided.")
    
    return {
        "url": data.url,
        "current_price": price,
        "target_price": data.target_price,
        "is_below_target": price <= data.target_price
    }
