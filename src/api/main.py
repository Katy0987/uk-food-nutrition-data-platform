from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import food_balance, household_spending, nutrition, prices

# Create FastAPI application
app = FastAPI(
    title="Food Data API",
    description="API for accessing food balance, household spending, and nutrition data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(food_balance.router)
app.include_router(household_spending.router)
app.include_router(nutrition.router)
app.include_router(prices.router)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Food Data API",
        "version": "1.0.0",
        "endpoints": {
            "food_balance": "/food-balance",
            "household_spending": "/household-spending",
            "nutrition": "/nutrition",
            "prices": "/prices",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)