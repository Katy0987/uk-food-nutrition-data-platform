from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from src.core.models.food import FoodBalance
from src.api.schemas.food_balance import FoodBalanceFilter


class FoodBalanceRepository:
    """Repository for FoodBalance data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[FoodBalance]:
        """Get all food balance records with pagination"""
        return self.db.query(FoodBalance).offset(skip).limit(limit).all()
    
    def get_by_primary_key(self, food_label: str, year: int, unit: str) -> Optional[FoodBalance]:
        """Get a specific food balance record by composite primary key (food_label, years, unit)"""
        return self.db.query(FoodBalance).filter(
            and_(
                FoodBalance.food_label == food_label,
                FoodBalance.years == year,
                FoodBalance.unit == unit
            )
        ).first()
    
    def get_by_food_label(self, food_label: str) -> List[FoodBalance]:
        """Get all records for a specific food label"""
        return self.db.query(FoodBalance).filter(
            FoodBalance.food_label == food_label
        ).all()
    
    def get_by_year(self, year: int) -> List[FoodBalance]:
        """Get all records for a specific year"""
        return self.db.query(FoodBalance).filter(
            FoodBalance.years == year
        ).all()
    
    def get_by_unit(self, unit: str) -> List[FoodBalance]:
        """Get all records for a specific unit"""
        return self.db.query(FoodBalance).filter(
            FoodBalance.unit == unit
        ).all()
    
    def get_filtered(self, filters: FoodBalanceFilter, skip: int = 0, limit: int = 100) -> List[FoodBalance]:
        """Get filtered food balance records"""
        query = self.db.query(FoodBalance)
        
        if filters.food_label:
            query = query.filter(FoodBalance.food_label.ilike(f"%{filters.food_label}%"))
        
        if filters.years:
            query = query.filter(FoodBalance.years == filters.years)
        
        if filters.min_year:
            query = query.filter(FoodBalance.years >= filters.min_year)
        
        if filters.max_year:
            query = query.filter(FoodBalance.years <= filters.max_year)
        
        if filters.unit:
            query = query.filter(FoodBalance.unit == filters.unit)
        
        if filters.min_amount is not None:
            query = query.filter(FoodBalance.amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.filter(FoodBalance.amount <= filters.max_amount)
        
        return query.offset(skip).limit(limit).all()
    
    def get_unique_food_labels(self) -> List[str]:
        """Get all unique food labels"""
        results = self.db.query(FoodBalance.food_label).distinct().all()
        return [r[0] for r in results]
    
    def get_unique_years(self) -> List[int]:
        """Get all unique years"""
        results = self.db.query(FoodBalance.years).distinct().order_by(FoodBalance.years).all()
        return [r[0] for r in results]
    
    def get_unique_units(self) -> List[str]:
        """Get all unique units"""
        results = self.db.query(FoodBalance.unit).distinct().all()
        return [r[0] for r in results if r[0] is not None]