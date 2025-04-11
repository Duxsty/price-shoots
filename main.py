from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from scraper import get_price

app = FastAPI()

class PriceRequest(BaseModel):
    url: str
    target_price: float

@app.post("/track-price")
async def track_price(data: PriceRequest):
    print(f"📥 Received request: {data.url} with target {data.target_price}")

    try:
        price = get_price(data.url)
        print(f"🔍 Scraped price: {price}")

        if price is None:
            raise HTTPException(status_code=404, detail="Unable to retrieve price from the URL provided.")

        return {"price": price, "below_target": price <= data.target_price}

    except Exception as e:
        print(f"❌ Error while processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error.")
