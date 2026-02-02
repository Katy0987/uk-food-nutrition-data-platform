# Placeholder for future price service
from sqlalchemy.orm import Session


class PriceService:
    """Service layer for price-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Add price-related methods here when price data is available
    pass