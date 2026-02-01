from sqlalchemy.orm import Session
from typing import List, Optional
from src.core.models.nutrition import Nutrition
from src.api.schemas.nutrition import NutritionFilter


class NutritionRepository:
    """Repository for Nutrition data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Nutrition]:
        """Get all nutrition records with pagination"""
        return self.db.query(Nutrition).offset(skip).limit(limit).all()
    
    def get_by_food_name(self, food_name: str) -> Optional[Nutrition]:
        """Get a specific nutrition record by food name (primary key)"""
        return self.db.query(Nutrition).filter(
            Nutrition.food_name == food_name
        ).first()
    
    def search_by_name(self, search_term: str) -> List[Nutrition]:
        """Search nutrition records by food name"""
        return self.db.query(Nutrition).filter(
            Nutrition.food_name.ilike(f"%{search_term}%")
        ).all()
    
    def get_filtered(self, filters: NutritionFilter, skip: int = 0, limit: int = 100) -> List[Nutrition]:
        """Get filtered nutrition records"""
        query = self.db.query(Nutrition)
        
        if filters.food_name:
            query = query.filter(Nutrition.food_name.ilike(f"%{filters.food_name}%"))
        
        # Energy filters
        if filters.min_energy_kcal is not None:
            query = query.filter(Nutrition.energy_kcal >= filters.min_energy_kcal)
        if filters.max_energy_kcal is not None:
            query = query.filter(Nutrition.energy_kcal <= filters.max_energy_kcal)
        
        # Protein filters
        if filters.min_protein_g is not None:
            query = query.filter(Nutrition.protein_g >= filters.min_protein_g)
        if filters.max_protein_g is not None:
            query = query.filter(Nutrition.protein_g <= filters.max_protein_g)
        
        # Fat filters
        if filters.min_fat_g is not None:
            query = query.filter(Nutrition.fat_g >= filters.min_fat_g)
        if filters.max_fat_g is not None:
            query = query.filter(Nutrition.fat_g <= filters.max_fat_g)
        
        # Carbohydrate filters
        if filters.min_carbohydrate_g is not None:
            query = query.filter(Nutrition.carbohydrate_g >= filters.min_carbohydrate_g)
        if filters.max_carbohydrate_g is not None:
            query = query.filter(Nutrition.carbohydrate_g <= filters.max_carbohydrate_g)
        
        return query.offset(skip).limit(limit).all()
    
    def get_high_protein_foods(self, min_protein: float = 10.0, skip: int = 0, limit: int = 100) -> List[Nutrition]:
        """Get foods with high protein content"""
        return self.db.query(Nutrition).filter(
            Nutrition.protein_g >= min_protein
        ).order_by(Nutrition.protein_g.desc()).offset(skip).limit(limit).all()
    
    def get_low_calorie_foods(self, max_calories: float = 100.0, skip: int = 0, limit: int = 100) -> List[Nutrition]:
        """Get low calorie foods"""
        return self.db.query(Nutrition).filter(
            Nutrition.energy_kcal <= max_calories
        ).order_by(Nutrition.energy_kcal.asc()).offset(skip).limit(limit).all()