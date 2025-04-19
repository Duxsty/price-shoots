from fastapi import FastAPI

app = FastAPI(
    title="PriceShoots API",
    description="Simplified backend for PriceShoots using PriceSpy redirect",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "API is running."}
