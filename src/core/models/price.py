from sqlalchemy import Column, String, Float, Text, DateTime, ARRAY, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class FoodPrice(Base):
    """
    SQLAlchemy model for food price and nutrition data.
    Adapted from the urban property model structure.
    """
    __tablename__ = "food_prices"

    # Primary key (UUID-style string)
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    # URLs and Metadata
    url = Column(String(500), unique=True, nullable=True, index=True)
    source = Column(String(50), default="tesco", index=True) # e.g., 'tesco', 'sainsburys'
    scraped_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())

    # Product Information
    product_name = Column(String(250), nullable=False, index=True)
    category = Column(String(100), index=True) # e.g., 'Dairy', 'Bakery'
    brand = Column(String(100), index=True)
    
    # Price Details
    price = Column(Float, index=True) # 1.55
    unit = Column(String(10), default="GBP") # 'GBP', 'p'
    price_per_unit = Column(String(50)) # e.g., '£0.15/100ml'

    # Content & Description
    description = Column(Text)
    image = Column(Text) # URL to product image

    # Semi-structured Data (Nutrition & Ingredients)
    # We use JSON for MongoDB-like flexibility within the SQL structure
    nutrition = Column(JSON, default={}) 
    ingredients = Column(Text)

    # Tags
    tags = Column(ARRAY(String), default=[])

    def __repr__(self):
        return f"<FoodPrice(source='{self.source}', name='{self.product_name}', price={self.price})>"

    @classmethod
    def from_scraped_item(cls, item_dict):
        """
        Maps raw scraped dictionary data to the SQLAlchemy model.
        """
        return cls(
            id=item_dict.get('id', str(uuid.uuid4())),
            url=item_dict.get('url'),
            source=item_dict.get('source', 'tesco'),
            product_name=item_dict.get('product_name'),
            category=item_dict.get('category'),
            brand=item_dict.get('brand'),
            price=item_dict.get('price'),
            unit=item_dict.get('unit', 'GBP'),
            price_per_unit=item_dict.get('price_per_unit'),
            description=item_dict.get('description'),
            image=item_dict.get('image'),
            nutrition=item_dict.get('nutrition', {}),
            ingredients=item_dict.get('ingredients'),
            tags=item_dict.get('tags', [])
        )

    def to_dict(self):
        """Convert the SQLAlchemy model instance to a dictionary for MongoDB ingestion."""
        return {
            'id': self.id,
            'source': self.source,
            'url': self.url,
            'scraped_date': self.scraped_date.isoformat() if self.scraped_date else None,
            'product_name': self.product_name,
            'category': self.category,
            'brand': self.brand,
            'price': self.price,
            'unit': self.unit,
            'price_per_unit': self.price_per_unit,
            'description': self.description,
            'image': self.image,
            'nutrition': self.nutrition,
            'ingredients': self.ingredients,
            'tags': self.tags,
        }