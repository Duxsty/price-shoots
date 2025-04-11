from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper import get_amazon_price

app = FastAPI()

class TrackRequest(BaseModel):
    url: str
    target_price: float

@app.post("/track-price")
def track_price(req: TrackRequest):
    try:
      {
  "current_price": 34.99,
  "target_price": 35.00,
  "alert": true
}

        if current_price is None:
            raise HTTPException(status_code=404, detail="Price not found.")
        return {
            "url": req.url,
            "target_price": req.target_price,
            "current_price": current_price,
            "alert": current_price <= req.target_price
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
