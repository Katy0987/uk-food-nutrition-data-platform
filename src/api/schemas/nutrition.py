from pydantic import BaseModel, Field, field_validator
from typing import Optional


class NutritionBase(BaseModel):
    food_name: str = Field(..., description="Name of the food item (text)")
    energy_kcal: Optional[float] = Field(None, description="Energy in kcal per 100g (numeric/double precision)")
    fat_g: Optional[float] = Field(None, description="Fat content in grams per 100g (double precision)")
    saturates_g: Optional[float] = Field(None, description="Saturated fat in grams per 100g (double precision)")
    carbohydrate_g: Optional[float] = Field(None, description="Carbohydrate in grams per 100g (double precision)")
    sugars_g: Optional[float] = Field(None, description="Sugars in grams per 100g (double precision)")
    starch_g: Optional[float] = Field(None, description="Starch in grams per 100g (double precision)")
    fibre_g: Optional[float] = Field(None, description="Fibre in grams per 100g (double precision)")
    protein_g: Optional[float] = Field(None, description="Protein in grams per 100g (double precision)")
    salt_g: Optional[float] = Field(None, description="Salt in grams per 100g (double precision)")
    
    @field_validator(
        'energy_kcal', 'fat_g', 'saturates_g', 'carbohydrate_g', 
        'sugars_g', 'starch_g', 'fibre_g', 'protein_g', 'salt_g',
        mode='before'
    )
    @classmethod
    def handle_na_values(cls, v):
        """Handle NA/None values for all numeric fields"""
        if v is None or (isinstance(v, str) and v.upper() in ['NA', 'NULL', '', 'NAN']):
            return None
        return v


class NutritionCreate(NutritionBase):
    """Schema for creating nutrition records"""
    pass


class NutritionResponse(NutritionBase):
    """Schema for nutrition response"""
    
    class Config:
        from_attributes = True


class NutritionFilter(BaseModel):
    """Schema for filtering nutrition data"""
    food_name: Optional[str] = Field(None, description="Filter by food name (partial match)")
    min_energy_kcal: Optional[float] = Field(None, description="Minimum energy in kcal")
    max_energy_kcal: Optional[float] = Field(None, description="Maximum energy in kcal")
    min_protein_g: Optional[float] = Field(None, description="Minimum protein in grams")
    max_protein_g: Optional[float] = Field(None, description="Maximum protein in grams")
    min_fat_g: Optional[float] = Field(None, description="Minimum fat in grams")
    max_fat_g: Optional[float] = Field(None, description="Maximum fat in grams")
    min_carbohydrate_g: Optional[float] = Field(None, description="Minimum carbohydrate in grams")
    max_carbohydrate_g: Optional[float] = Field(None, description="Maximum carbohydrate in grams")
    min_fibre_g: Optional[float] = Field(None, description="Minimum fibre in grams")
    max_fibre_g: Optional[float] = Field(None, description="Maximum fibre in grams")