"""
SQLAlchemy model for Open Food Facts product eco-score data.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Index, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ProductEco(Base):
    """
    Cached Open Food Facts product data with eco-scores.
    Stores environmental impact and nutrition data.
    """

    __tablename__ = "product_eco"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Product Identification
    barcode = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic Product Information
    product_name = Column(String(255), index=True)
    generic_name = Column(String(255))
    brands = Column(String(255), index=True)
    brands_tags = Column(Text)  # JSON array as text
    
    # Categories
    categories = Column(Text, index=True)
    categories_tags = Column(Text)  # JSON array as text
    main_category = Column(String(100), index=True)
    
    # Eco-Score (Environmental Impact)
    ecoscore_grade = Column(String(1), index=True)  # a, b, c, d, e
    ecoscore_score = Column(Integer, index=True)  # 0-100
    ecoscore_data = Column(JSON)  # Detailed eco-score breakdown
    
    # Nutri-Score (Nutritional Quality)
    nutriscore_grade = Column(String(1), index=True)  # a, b, c, d, e
    nutriscore_score = Column(Integer)
    nutrition_grade_fr = Column(String(1))  # Legacy field
    
    # Environmental Impact Details
    carbon_footprint_100g = Column(Float)  # g CO2 per 100g
    carbon_footprint_from_known_ingredients_100g = Column(Float)
    
    # Manufacturing and Packaging
    manufacturing_places = Column(Text)
    manufacturing_places_tags = Column(Text)
    origins = Column(Text)
    origins_tags = Column(Text)
    packaging = Column(Text)
    packaging_tags = Column(Text)
    
    # Impact Scores
    manufacturing_impact = Column(String(50))  # low, medium, high
    packaging_impact = Column(String(50))
    transportation_impact = Column(String(50))
    
    # Labels and Certifications
    labels = Column(Text)
    labels_tags = Column(Text)  # organic, fair-trade, etc.
    
    # Quantities
    quantity = Column(String(50))
    serving_size = Column(String(50))
    
    # Images
    image_url = Column(Text)
    image_small_url = Column(Text)
    image_ingredients_url = Column(Text)
    image_nutrition_url = Column(Text)
    
    # Nutrition Facts (per 100g)
    energy_100g = Column(Float)
    fat_100g = Column(Float)
    saturated_fat_100g = Column(Float)
    carbohydrates_100g = Column(Float)
    sugars_100g = Column(Float)
    fiber_100g = Column(Float)
    proteins_100g = Column(Float)
    salt_100g = Column(Float)
    
    # Ingredients
    ingredients_text = Column(Text)
    ingredients_count = Column(Integer)
    
    # Additional Metadata
    countries = Column(Text)
    countries_tags = Column(Text)
    stores = Column(Text)
    stores_tags = Column(Text)
    
    # Data Quality
    completeness = Column(Float)  # 0.0 to 1.0
    data_quality_warnings = Column(Text)
    
    # Source Information
    creator = Column(String(100))
    created_t = Column(Integer)  # Unix timestamp from OFF
    last_modified_t = Column(Integer)  # Unix timestamp from OFF
    
    # Cache Management
    cached_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_ecoscore', 'ecoscore_grade', 'ecoscore_score'),
        Index('idx_nutriscore', 'nutriscore_grade'),
        Index('idx_categories_ecoscore', 'main_category', 'ecoscore_grade'),
        Index('idx_brands_ecoscore', 'brands', 'ecoscore_grade'),
        Index('idx_cached_at', 'cached_at'),
    )

    def __repr__(self) -> str:
        return (
            f"<ProductEco(barcode={self.barcode}, "
            f"name='{self.product_name}', "
            f"ecoscore='{self.ecoscore_grade}', "
            f"nutriscore='{self.nutriscore_grade}')>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "barcode": self.barcode,
            "product_name": self.product_name,
            "generic_name": self.generic_name,
            "brands": self.brands,
            "categories": self.categories,
            "main_category": self.main_category,
            "ecoscore": {
                "grade": self.ecoscore_grade,
                "score": self.ecoscore_score,
                "data": self.ecoscore_data,
            },
            "nutriscore": {
                "grade": self.nutriscore_grade,
                "score": self.nutriscore_score,
            },
            "environmental_impact": {
                "carbon_footprint_100g": self.carbon_footprint_100g,
                "manufacturing_impact": self.manufacturing_impact,
                "packaging_impact": self.packaging_impact,
                "transportation_impact": self.transportation_impact,
            },
            "packaging": self.packaging,
            "manufacturing_places": self.manufacturing_places,
            "origins": self.origins,
            "labels": self.labels,
            "quantity": self.quantity,
            "serving_size": self.serving_size,
            "images": {
                "url": self.image_url,
                "small": self.image_small_url,
                "ingredients": self.image_ingredients_url,
                "nutrition": self.image_nutrition_url,
            },
            "nutrition_per_100g": {
                "energy": self.energy_100g,
                "fat": self.fat_100g,
                "saturated_fat": self.saturated_fat_100g,
                "carbohydrates": self.carbohydrates_100g,
                "sugars": self.sugars_100g,
                "fiber": self.fiber_100g,
                "proteins": self.proteins_100g,
                "salt": self.salt_100g,
            },
            "ingredients": {
                "text": self.ingredients_text,
                "count": self.ingredients_count,
            },
            "completeness": self.completeness,
            "cached_at": self.cached_at.isoformat() if self.cached_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_stale(self, hours: int = 24) -> bool:
        """Check if cached data is stale."""
        if not self.cached_at:
            return True
        age = datetime.utcnow() - self.cached_at
        return age.total_seconds() > (hours * 3600)

    @property
    def is_eco_friendly(self) -> bool:
        """Check if product has good eco-score (A or B)."""
        return self.ecoscore_grade in ["a", "b"] if self.ecoscore_grade else False

    @property
    def is_healthy(self) -> bool:
        """Check if product has good nutri-score (A or B)."""
        return self.nutriscore_grade in ["a", "b"] if self.nutriscore_grade else False

    @property
    def overall_score(self) -> Optional[float]:
        """Calculate overall score combining eco and nutri scores (0-100)."""
        if self.ecoscore_score is not None and self.nutriscore_score is not None:
            return (self.ecoscore_score + self.nutriscore_score) / 2
        return None