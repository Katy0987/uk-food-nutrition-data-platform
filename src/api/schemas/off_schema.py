"""
Pydantic schemas for Open Food Facts API responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class OFFNutrition(BaseModel):
    """Nutrition facts per 100g."""
    energy_100g: Optional[float] = None
    fat_100g: Optional[float] = None
    saturated_fat_100g: Optional[float] = None
    carbohydrates_100g: Optional[float] = None
    sugars_100g: Optional[float] = None
    fiber_100g: Optional[float] = None
    proteins_100g: Optional[float] = None
    salt_100g: Optional[float] = None


class OFFEcoScore(BaseModel):
    """Eco-score information."""
    grade: Optional[str] = Field(None, description="Eco-score grade (a-e)")
    score: Optional[int] = Field(None, description="Eco-score (0-100)")


class OFFNutriScore(BaseModel):
    """Nutri-score information."""
    grade: Optional[str] = Field(None, description="Nutri-score grade (a-e)")
    score: Optional[int] = None


class OFFEnvironmentalImpact(BaseModel):
    """Environmental impact data."""
    carbon_footprint_100g: Optional[float] = Field(None, description="CO2 emissions per 100g")
    manufacturing_impact: Optional[str] = None
    packaging_impact: Optional[str] = None
    transportation_impact: Optional[str] = None


class OFFImages(BaseModel):
    """Product images."""
    url: Optional[str] = None
    small: Optional[str] = None
    ingredients: Optional[str] = None
    nutrition: Optional[str] = None


class OFFProductBase(BaseModel):
    """Base product information."""
    barcode: str = Field(..., description="Product barcode")
    product_name: Optional[str] = None
    brands: Optional[str] = None
    categories: Optional[str] = None
    quantity: Optional[str] = None
    ecoscore: Optional[OFFEcoScore] = None
    nutriscore: Optional[OFFNutriScore] = None
    images: Optional[OFFImages] = None


class OFFProductDetail(OFFProductBase):
    """Detailed product information."""
    generic_name: Optional[str] = None
    main_category: Optional[str] = None
    environmental_impact: Optional[OFFEnvironmentalImpact] = None
    nutrition: Optional[OFFNutrition] = None
    ingredients_text: Optional[str] = None
    labels: Optional[str] = None
    manufacturing_places: Optional[str] = None
    origins: Optional[str] = None
    packaging: Optional[str] = None
    serving_size: Optional[str] = None
    completeness: Optional[float] = None
    cached_at: Optional[datetime] = None


class OFFProductResponse(BaseModel):
    """Response for single product."""
    success: bool = True
    data: OFFProductDetail


class OFFSearchResponse(BaseModel):
    """Response for product search."""
    products: List[OFFProductBase]
    meta: dict = Field(default_factory=dict)


class OFFCompareResponse(BaseModel):
    """Response for product comparison."""
    success: bool = True
    data: List[OFFProductDetail]
    meta: Optional[dict] = None