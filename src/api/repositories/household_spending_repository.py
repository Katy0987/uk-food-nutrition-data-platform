from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from src.core.models.food import HouseholdSpending
from src.api.schemas.household_spending import HouseholdSpendingFilter


class HouseholdSpendingRepository:
    """Repository for HouseholdSpending data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[HouseholdSpending]:
        """Get all household spending records with pagination"""
        return self.db.query(HouseholdSpending).offset(skip).limit(limit).all()
    
    def get_by_food_code_and_year(self, food_code: str, year: int) -> Optional[HouseholdSpending]:
        """Get a specific household spending record by primary key"""
        return self.db.query(HouseholdSpending).filter(
            and_(
                HouseholdSpending.food_code == food_code,
                HouseholdSpending.years == year
            )
        ).first()
    
    def get_by_food_code(self, food_code: str) -> List[HouseholdSpending]:
        """Get all records for a specific food code"""
        return self.db.query(HouseholdSpending).filter(
            HouseholdSpending.food_code == food_code
        ).all()
    
    def get_by_year(self, year: int) -> List[HouseholdSpending]:
        """Get all records for a specific year"""
        return self.db.query(HouseholdSpending).filter(
            HouseholdSpending.years == year
        ).all()
    
    def get_filtered(self, filters: HouseholdSpendingFilter, skip: int = 0, limit: int = 100) -> List[HouseholdSpending]:
        """Get filtered household spending records"""
        query = self.db.query(HouseholdSpending)
        
        if filters.food_code:
            query = query.filter(HouseholdSpending.food_code.ilike(f"%{filters.food_code}%"))
        
        if filters.years:
            query = query.filter(HouseholdSpending.years == filters.years)
        
        if filters.min_year:
            query = query.filter(HouseholdSpending.years >= filters.min_year)
        
        if filters.max_year:
            query = query.filter(HouseholdSpending.years <= filters.max_year)
        
        if filters.units:
            query = query.filter(HouseholdSpending.units == filters.units)
        
        if filters.rse_indicator:
            query = query.filter(HouseholdSpending.rse_indicator == filters.rse_indicator)
        
        if filters.min_amount is not None:
            query = query.filter(HouseholdSpending.amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.filter(HouseholdSpending.amount <= filters.max_amount)
        
        return query.offset(skip).limit(limit).all()
    
    def get_unique_food_codes(self) -> List[str]:
        """Get all unique food codes"""
        results = self.db.query(HouseholdSpending.food_code).distinct().all()
        return [r[0] for r in results]
    
    def get_unique_years(self) -> List[int]:
        """Get all unique years"""
        results = self.db.query(HouseholdSpending.years).distinct().order_by(HouseholdSpending.years).all()
        return [r[0] for r in results]