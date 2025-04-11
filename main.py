from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper import get_price

app = FastAPI()

class TrackRequest(BaseModel):
    url: str
    target_price: float

@app.get("/")
def root():
    return {"status": "API running!"}

@app.post("/track-price")
def track_price(data: TrackRequest):
    price = get_price(data.url)

    if price is None:
        raise HTTPException(status_code=404, detail="Price not found.")

    return {
        "current_price": price,
        "target_price": data.target_price,
        "is_below_target": price <= data.target_price
    }

