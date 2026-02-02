from fastapi import APIRouter

router = APIRouter(prefix="/prices", tags=["Prices"])


@router.get("/")
def get_prices():
    """
    Placeholder endpoint for price data
    """
    return {"message": "Price endpoints will be implemented when price data is available"}