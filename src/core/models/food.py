from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ARRAY, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class FoodItem(Base):
    __tablename__ = "food_items"

    # Primary key (UUID for unique tracking across sources)
    id = Column(String(32), primary_key=True, index=True, default=lambda: uuid.uuid4().hex)

    # URLs and Metadata
    url = Column(String(500), unique=True, nullable=False, index=True)
    source = Column(String(50), default="mcdonalds", index=True)
    scraped_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())

    # Item information
    product_name = Column(String(200), index=True)
    category = Column(String(100), index=True) # e.g., "Burgers", "Breakfast", "Fries & Sides"
    description = Column(Text)
    image_url = Column(Text)

    # Pricing (Base price for standard size)
    price = Column(Float, index=True) 
    currency = Column(String(10), default="GBP")

    # Size Variations (McDonald's specific: e.g., Small, Medium, Large)
    # Stored as a list of dicts: [{"size": "Large", "price": 1.99, "calories": 444}]
    variations = Column(JSON, default=[])

    # Nutritional Information
    calories = Column(Integer, index=True) # Total kcal
    nutrition_details = Column(JSON, default={}) # { "fat": "25g", "protein": "30g", "carbs": "45g" }
    
    # Diet and Allergens
    allergens = Column(ARRAY(String), default=[]) # ["Milk", "Wheat", "Sesame"]
    is_vegetarian = Column(Boolean, default=False, index=True)
    is_vegan = Column(Boolean, default=False, index=True)

    # Meta Tags
    tags = Column(ARRAY(String), default=[]) # ["Saver Menu", "Limited Time", "Main"]

    def __repr__(self):
        return f"<FoodItem(id='{self.id}', name='{self.product_name}', price={self.price})>"

    @classmethod
    def from_scraped_item(cls, item):
        """
        Maps a scraped dictionary (from your scraper) to this model.
        """
        return cls(
            id=item.get('id', uuid.uuid4().hex),
            url=item.get('url'),
            source=item.get('source', 'mcdonalds'),
            product_name=item.get('product_name'),
            category=item.get('category'),
            description=item.get('description'),
            image_url=item.get('image_url'),
            price=item.get('price'),
            currency=item.get('currency', 'GBP'),
            variations=item.get('variations', []),
            calories=item.get('calories'),
            nutrition_details=item.get('nutrition_details', {}),
            allergens=item.get('allergens', []),
            is_vegetarian=item.get('is_vegetarian', False),
            is_vegan=item.get('is_vegan', False),
            tags=item.get('tags', []),
        )

    def to_dict(self):
        """
        Convert to dictionary format for MongoDB storage.
        """
        return {
            'id': self.id,
            'url': self.url,
            'source': self.source,
            'scraped_date': self.scraped_date.isoformat() if self.scraped_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'product_name': self.product_name,
            'category': self.category,
            'description': self.description,
            'image_url': self.image_url,
            'price': self.price,
            'currency': self.currency,
            'variations': self.variations,
            'calories': self.calories,
            'nutrition_details': self.nutrition_details,
            'allergens': self.allergens,
            'is_vegetarian': self.is_vegetarian,
            'is_vegan': self.is_vegan,
            'tags': self.tags,
        }