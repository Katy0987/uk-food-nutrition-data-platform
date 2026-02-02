from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from src.api.repositories.food_balance_repository import FoodBalanceRepository
from src.api.repositories.household_spending_repository import HouseholdSpendingRepository
from src.api.repositories.nutrition_repository import NutritionRepository
from src.api.schemas.food_balance import FoodBalanceFilter, FoodBalanceResponse
from src.api.schemas.household_spending import HouseholdSpendingFilter, HouseholdSpendingResponse
from src.api.schemas.nutrition import NutritionFilter, NutritionResponse


class FoodService:
    """Service layer for food-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.food_balance_repo = FoodBalanceRepository(db)
        self.household_spending_repo = HouseholdSpendingRepository(db)
        self.nutrition_repo = NutritionRepository(db)
    
    # Food Balance Methods
    def get_food_balance_data(self, skip: int = 0, limit: int = 100) -> List[FoodBalanceResponse]:
        """Get all food balance data"""
        records = self.food_balance_repo.get_all(skip, limit)
        return [FoodBalanceResponse.from_orm(record) for record in records]
    
    def get_food_balance_by_filters(self, filters: FoodBalanceFilter, skip: int = 0, limit: int = 100) -> List[FoodBalanceResponse]:
        """Get filtered food balance data"""
        records = self.food_balance_repo.get_filtered(filters, skip, limit)
        return [FoodBalanceResponse.from_orm(record) for record in records]
    
    def get_food_balance_metadata(self) -> Dict[str, Any]:
        """Get metadata about food balance data"""
        return {
            "unique_food_labels": self.food_balance_repo.get_unique_food_labels(),
            "unique_years": self.food_balance_repo.get_unique_years()
        }
    
    # Household Spending Methods
    def get_household_spending_data(self, skip: int = 0, limit: int = 100) -> List[HouseholdSpendingResponse]:
        """Get all household spending data"""
        records = self.household_spending_repo.get_all(skip, limit)
        return [HouseholdSpendingResponse.from_orm(record) for record in records]
    
    def get_household_spending_by_filters(self, filters: HouseholdSpendingFilter, skip: int = 0, limit: int = 100) -> List[HouseholdSpendingResponse]:
        """Get filtered household spending data"""
        records = self.household_spending_repo.get_filtered(filters, skip, limit)
        return [HouseholdSpendingResponse.from_orm(record) for record in records]
    
    def get_household_spending_metadata(self) -> Dict[str, Any]:
        """Get metadata about household spending data"""
        return {
            "unique_food_codes": self.household_spending_repo.get_unique_food_codes(),
            "unique_years": self.household_spending_repo.get_unique_years()
        }
    
    # Nutrition Methods
    def get_nutrition_data(self, skip: int = 0, limit: int = 100) -> List[NutritionResponse]:
        """Get all nutrition data"""
        records = self.nutrition_repo.get_all(skip, limit)
        return [NutritionResponse.from_orm(record) for record in records]
    
    def get_nutrition_by_filters(self, filters: NutritionFilter, skip: int = 0, limit: int = 100) -> List[NutritionResponse]:
        """Get filtered nutrition data"""
        records = self.nutrition_repo.get_filtered(filters, skip, limit)
        return [NutritionResponse.from_orm(record) for record in records]
    
    def get_nutrition_by_name(self, food_name: str) -> Optional[NutritionResponse]:
        """Get nutrition data by food name"""
        record = self.nutrition_repo.get_by_food_name(food_name)
        return NutritionResponse.from_orm(record) if record else None
    
    def search_nutrition(self, search_term: str) -> List[NutritionResponse]:
        """Search nutrition data by food name"""
        records = self.nutrition_repo.search_by_name(search_term)
        return [NutritionResponse.from_orm(record) for record in records]