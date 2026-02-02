from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from src.api.database.session import get_db
from src.api.services.food_service import FoodService
from src.api.schemas.food_balance import FoodBalanceResponse, FoodBalanceFilter

router = APIRouter(prefix="/food-balance", tags=["Food Balance"])


@router.get("/", response_model=List[FoodBalanceResponse])
def get_food_balance_data(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all food balance data with pagination
    """
    service = FoodService(db)
    return service.get_food_balance_data(skip=skip, limit=limit)


@router.post("/filter", response_model=List[FoodBalanceResponse])
def filter_food_balance_data(
    filters: FoodBalanceFilter,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Filter food balance data based on criteria
    """
    service = FoodService(db)
    return service.get_food_balance_by_filters(filters=filters, skip=skip, limit=limit)


@router.get("/metadata")
def get_food_balance_metadata(db: Session = Depends(get_db)):
    """
    Get metadata about available food labels, years, and units
    """
    service = FoodService(db)
    metadata = service.get_food_balance_metadata()
    
    from src.api.repositories.food_balance_repository import FoodBalanceRepository
    repo = FoodBalanceRepository(db)
    metadata['unique_units'] = repo.get_unique_units()
    
    return metadata


@router.get("/by-primary-key", response_model=FoodBalanceResponse)
def get_by_primary_key(
    food_label: str = Query(..., description="Food label"),
    year: int = Query(..., description="Year"),
    unit: str = Query(..., description="Unit"),
    db: Session = Depends(get_db)
):
    """
    Get a specific record by composite primary key (food_label, year, unit)
    """
    from src.api.repositories.food_balance_repository import FoodBalanceRepository
    repo = FoodBalanceRepository(db)
    record = repo.get_by_primary_key(food_label, year, unit)
    
    if not record:
        raise HTTPException(
            status_code=404, 
            detail=f"No record found for food_label='{food_label}', year={year}, unit='{unit}'"
        )
    
    return FoodBalanceResponse.from_orm(record)


@router.get("/by-food-label/{food_label}", response_model=List[FoodBalanceResponse])
def get_by_food_label(
    food_label: str,
    db: Session = Depends(get_db)
):
    """
    Get all records for a specific food label
    """
    from src.api.repositories.food_balance_repository import FoodBalanceRepository
    repo = FoodBalanceRepository(db)
    records = repo.get_by_food_label(food_label)
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for food label: {food_label}")
    
    return [FoodBalanceResponse.from_orm(record) for record in records]


@router.get("/by-year/{year}", response_model=List[FoodBalanceResponse])
def get_by_year(
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get all records for a specific year
    """
    from src.api.repositories.food_balance_repository import FoodBalanceRepository
    repo = FoodBalanceRepository(db)
    records = repo.get_by_year(year)
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for year: {year}")
    
    return [FoodBalanceResponse.from_orm(record) for record in records]


@router.get("/by-unit/{unit}", response_model=List[FoodBalanceResponse])
def get_by_unit(
    unit: str,
    db: Session = Depends(get_db)
):
    """
    Get all records for a specific unit
    """
    from src.api.repositories.food_balance_repository import FoodBalanceRepository
    repo = FoodBalanceRepository(db)
    records = repo.get_by_unit(unit)
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for unit: {unit}")
    
    return [FoodBalanceResponse.from_orm(record) for record in records]