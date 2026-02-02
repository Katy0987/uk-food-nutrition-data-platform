from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal


class HouseholdSpendingBase(BaseModel):
    food_code: str = Field(..., description="Food category code (text)")
    units: Optional[str] = Field(None, description="Unit of measurement (text)")
    years: int = Field(..., ge=1900, le=2100, description="Year of the data (integer)")
    amount: Optional[Decimal] = Field(None, description="Spending amount (numeric)")
    rse_indicator: Optional[str] = Field(None, description="RSE indicator (text)")
    
    @field_validator('units', 'rse_indicator', 'amount', mode='before')
    @classmethod
    def handle_na_values(cls, v):
        """Handle NA/None values"""
        if v is None or (isinstance(v, str) and v.upper() in ['NA', 'NULL', '']):
            return None
        return v


class HouseholdSpendingCreate(HouseholdSpendingBase):
    """Schema for creating household spending records"""
    pass


class HouseholdSpendingResponse(HouseholdSpendingBase):
    """Schema for household spending response"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: float
        }


class HouseholdSpendingFilter(BaseModel):
    """Schema for filtering household spending data"""
    food_code: Optional[str] = Field(None, description="Filter by food code (partial match)")
    years: Optional[int] = Field(None, description="Filter by exact year")
    min_year: Optional[int] = Field(None, description="Filter by minimum year")
    max_year: Optional[int] = Field(None, description="Filter by maximum year")
    units: Optional[str] = Field(None, description="Filter by units (exact match)")
    rse_indicator: Optional[str] = Field(None, description="Filter by RSE indicator (exact match)")
    min_amount: Optional[Decimal] = Field(None, description="Filter by minimum amount")
    max_amount: Optional[Decimal] = Field(None, description="Filter by maximum amount")
    
    class Config:
        json_encoders = {
            Decimal: float
        }