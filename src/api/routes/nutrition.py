from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from src.api.database.session import get_db
from src.api.services.food_service import FoodService
from src.api.schemas.nutrition import NutritionResponse, NutritionFilter

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])


@router.get("/", response_model=List[NutritionResponse])
def get_nutrition_data(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all nutrition data with pagination
    """
    service = FoodService(db)
    return service.get_nutrition_data(skip=skip, limit=limit)


@router.post("/filter", response_model=List[NutritionResponse])
def filter_nutrition_data(
    filters: NutritionFilter,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Filter nutrition data based on criteria
    """
    service = FoodService(db)
    return service.get_nutrition_by_filters(filters=filters, skip=skip, limit=limit)


@router.get("/search/{search_term}", response_model=List[NutritionResponse])
def search_nutrition(
    search_term: str,
    db: Session = Depends(get_db)
):
    """
    Search nutrition data by food name
    """
    service = FoodService(db)
    results = service.search_nutrition(search_term)
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No nutrition data found matching: {search_term}")
    
    return results


@router.get("/by-name/{food_name}", response_model=NutritionResponse)
def get_by_food_name(
    food_name: str,
    db: Session = Depends(get_db)
):
    """
    Get nutrition data for a specific food item
    """
    service = FoodService(db)
    result = service.get_nutrition_by_name(food_name)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Nutrition data not found for: {food_name}")
    
    return result


@router.get("/high-protein", response_model=List[NutritionResponse])
def get_high_protein_foods(
    min_protein: float = Query(10.0, ge=0, description="Minimum protein content in grams"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get foods with high protein content
    """
    from src.api.repositories.nutrition_repository import NutritionRepository
    repo = NutritionRepository(db)
    records = repo.get_high_protein_foods(min_protein=min_protein, skip=skip, limit=limit)
    
    return [NutritionResponse.from_orm(record) for record in records]


@router.get("/low-calorie", response_model=List[NutritionResponse])
def get_low_calorie_foods(
    max_calories: float = Query(100.0, ge=0, description="Maximum calorie content in kcal"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get low calorie foods
    """
    from src.api.repositories.nutrition_repository import NutritionRepository
    repo = NutritionRepository(db)
    records = repo.get_low_calorie_foods(max_calories=max_calories, skip=skip, limit=limit)
    
    return [NutritionResponse.from_orm(record) for record in records]