from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal


class FoodBalanceBase(BaseModel):
    food_label: str = Field(..., description="Food category label (text)")
    years: int = Field(..., ge=1900, le=2100, description="Year of the data (integer)")
    unit: str = Field(..., description="Unit of measurement (text)")
    amount: Optional[Decimal] = Field(None, description="Amount value (numeric)")
    
    @field_validator('amount', mode='before')
    @classmethod
    def handle_na_amount(cls, v):
        """Handle NA/None values for amount"""
        if v is None or (isinstance(v, str) and v.upper() in ['NA', 'NULL', '']):
            return None
        return v


class FoodBalanceCreate(FoodBalanceBase):
    """Schema for creating food balance records"""
    pass


class FoodBalanceResponse(FoodBalanceBase):
    """Schema for food balance response"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: float  # Convert Decimal to float in JSON response
        }


class FoodBalanceFilter(BaseModel):
    """Schema for filtering food balance data"""
    food_label: Optional[str] = Field(None, description="Filter by food label (partial match)")
    years: Optional[int] = Field(None, description="Filter by exact year")
    min_year: Optional[int] = Field(None, description="Filter by minimum year")
    max_year: Optional[int] = Field(None, description="Filter by maximum year")
    unit: Optional[str] = Field(None, description="Filter by unit (exact match)")
    min_amount: Optional[Decimal] = Field(None, description="Filter by minimum amount")
    max_amount: Optional[Decimal] = Field(None, description="Filter by maximum amount")
    
    class Config:
        json_encoders = {
            Decimal: float
        }