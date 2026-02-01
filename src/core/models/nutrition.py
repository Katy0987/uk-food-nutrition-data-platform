from sqlalchemy import Column, String, Double
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Nutrition(Base):
    """
    SQLAlchemy model for nutrition table
    Represents nutritional information per 100g of food
    Primary key is food_name
    """
    __tablename__ = 'nutrition'
    
    food_name = Column(String, primary_key=True, nullable=False, comment="Name of the food item")
    energy_kcal = Column(Double, nullable=True, comment="Energy in kcal per 100g (can be NULL/NA)")
    fat_g = Column(Double, nullable=True, comment="Fat content in grams per 100g (can be NULL/NA)")
    saturates_g = Column(Double, nullable=True, comment="Saturated fat in grams per 100g (can be NULL/NA)")
    carbohydrate_g = Column(Double, nullable=True, comment="Carbohydrate in grams per 100g (can be NULL/NA)")
    sugars_g = Column(Double, nullable=True, comment="Sugars in grams per 100g (can be NULL/NA)")
    starch_g = Column(Double, nullable=True, comment="Starch in grams per 100g (can be NULL/NA)")
    fibre_g = Column(Double, nullable=True, comment="Fibre in grams per 100g (can be NULL/NA)")
    protein_g = Column(Double, nullable=True, comment="Protein in grams per 100g (can be NULL/NA)")
    salt_g = Column(Double, nullable=True, comment="Salt in grams per 100g (can be NULL/NA)")
    
    def __repr__(self):
        return f"<Nutrition(food_name='{self.food_name}', energy_kcal={self.energy_kcal}, protein_g={self.protein_g})>"
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'food_name': self.food_name,
            'energy_kcal': self.energy_kcal,
            'fat_g': self.fat_g,
            'saturates_g': self.saturates_g,
            'carbohydrate_g': self.carbohydrate_g,
            'sugars_g': self.sugars_g,
            'starch_g': self.starch_g,
            'fibre_g': self.fibre_g,
            'protein_g': self.protein_g,
            'salt_g': self.salt_g
        }