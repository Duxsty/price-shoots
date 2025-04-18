from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel
from playwright.async_api import async_playwright

router = APIRouter()

class PriceSpyResult(BaseModel):
    product_name: str
    price: float
    source: str
    link: str
    image: str

@router.get("/search-pricespy", response_model=List[PriceSpyResult])
async def search_pricespy(q: str = Query(...)):
