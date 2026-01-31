"""
SQLAlchemy model for FSA establishment data (cached hygiene ratings).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Establishment(Base):
    """
    Cached FSA establishment data with hygiene ratings.
    Stores data from Food Standards Agency API.
    """

    __tablename__ = "establishments"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # FSA Unique ID
    fhrsid = Column(Integer, unique=True, nullable=False, index=True)
    
    # Business Information
    business_name = Column(String(255), nullable=False, index=True)
    business_type = Column(String(100))
    business_type_id = Column(Integer)
    
    # Address Information
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    address_line_3 = Column(String(255))
    address_line_4 = Column(String(255))
    postcode = Column(String(10), index=True)
    
    # Rating Information
    rating_value = Column(String(10), index=True)  # Can be '0'-'5', 'AwaitingInspection', 'Exempt'
    rating_date = Column(DateTime)
    rating_key = Column(String(50))
    
    # Scores (lower is better, 0 is best)
    hygiene_score = Column(Integer)
    structural_score = Column(Integer)
    confidence_in_management_score = Column(Integer)
    
    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Authority Information
    local_authority_code = Column(Integer)
    local_authority_name = Column(String(100), index=True)
    local_authority_website = Column(Text)
    local_authority_email = Column(String(255))
    
    # Additional Information
    scheme_type = Column(String(50))
    new_rating_pending = Column(String(10))
    right_to_reply = Column(Text)
    
    # Geocode
    geocode_longitude = Column(Float)
    geocode_latitude = Column(Float)
    
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
        Index('idx_postcode_rating', 'postcode', 'rating_value'),
        Index('idx_location', 'latitude', 'longitude'),
        Index('idx_business_name_postcode', 'business_name', 'postcode'),
        Index('idx_local_authority_rating', 'local_authority_name', 'rating_value'),
        Index('idx_establishments_cached_at', 'cached_at'),
    )

    def __repr__(self) -> str:
        return (
            f"<Establishment(fhrsid={self.fhrsid}, "
            f"name='{self.business_name}', "
            f"rating='{self.rating_value}', "
            f"postcode='{self.postcode}')>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "fhrsid": self.fhrsid,
            "business_name": self.business_name,
            "business_type": self.business_type,
            "business_type_id": self.business_type_id,
            "address": {
                "line1": self.address_line_1,
                "line2": self.address_line_2,
                "line3": self.address_line_3,
                "line4": self.address_line_4,
                "postcode": self.postcode,
            },
            "rating": {
                "value": self.rating_value,
                "date": self.rating_date.isoformat() if self.rating_date else None,
                "key": self.rating_key,
            },
            "scores": {
                "hygiene": self.hygiene_score,
                "structural": self.structural_score,
                "confidence_in_management": self.confidence_in_management_score,
            },
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "local_authority": {
                "code": self.local_authority_code,
                "name": self.local_authority_name,
                "website": self.local_authority_website,
                "email": self.local_authority_email,
            },
            "scheme_type": self.scheme_type,
            "new_rating_pending": self.new_rating_pending,
            "right_to_reply": self.right_to_reply,
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
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [
            self.address_line_1,
            self.address_line_2,
            self.address_line_3,
            self.address_line_4,
            self.postcode,
        ]
        return ", ".join(filter(None, parts))

    @property
    def total_score(self) -> Optional[int]:
        """Calculate total hygiene score (sum of all scores)."""
        scores = [
            self.hygiene_score,
            self.structural_score,
            self.confidence_in_management_score,
        ]
        if all(s is not None for s in scores):
            return sum(scores)
        return None