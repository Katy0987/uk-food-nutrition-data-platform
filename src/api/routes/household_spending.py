from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from src.api.database.session import get_db
from src.api.services.food_service import FoodService
from src.api.schemas.household_spending import HouseholdSpendingResponse, HouseholdSpendingFilter

router = APIRouter(prefix="/household-spending", tags=["Household Spending"])


@router.get("/", response_model=List[HouseholdSpendingResponse])
def get_household_spending_data(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all household spending data with pagination
    """
    service = FoodService(db)
    return service.get_household_spending_data(skip=skip, limit=limit)


@router.post("/filter", response_model=List[HouseholdSpendingResponse])
def filter_household_spending_data(
    filters: HouseholdSpendingFilter,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Filter household spending data based on criteria
    """
    service = FoodService(db)
    return service.get_household_spending_by_filters(filters=filters, skip=skip, limit=limit)


@router.get("/metadata")
def get_household_spending_metadata(db: Session = Depends(get_db)):
    """
    Get metadata about available food codes and years
    """
    service = FoodService(db)
    return service.get_household_spending_metadata()


@router.get("/by-food-code/{food_code}", response_model=List[HouseholdSpendingResponse])
def get_by_food_code(
    food_code: str,
    db: Session = Depends(get_db)
):
    """
    Get all records for a specific food code
    """
    from src.api.repositories.household_spending_repository import HouseholdSpendingRepository
    repo = HouseholdSpendingRepository(db)
    records = repo.get_by_food_code(food_code)
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for food code: {food_code}")
    
    return [HouseholdSpendingResponse.from_orm(record) for record in records]


@router.get("/by-year/{year}", response_model=List[HouseholdSpendingResponse])
def get_by_year(
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get all records for a specific year
    """
    from src.api.repositories.household_spending_repository import HouseholdSpendingRepository
    repo = HouseholdSpendingRepository(db)
    records = repo.get_by_year(year)
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for year: {year}")
    
    return [HouseholdSpendingResponse.from_orm(record) for record in records]