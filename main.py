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
    current_price = get_price(data.url)

    if current_price is None:
        raise HTTPException(status_code=404, detail="Unable to retrieve price from the URL provided.")

    return {
        "current_price": current_price,
        "target_price": data.target_price,
        "is_below_target": current_price <= data.target_price
    }
