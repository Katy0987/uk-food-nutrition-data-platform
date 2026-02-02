"""
Pydantic schemas for FSA (Food Standards Agency) API responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class FSAScores(BaseModel):
    """Hygiene scores from FSA inspection."""
    hygiene: Optional[int] = Field(None, description="Hygiene score (0-30, lower is better)")
    structural: Optional[int] = Field(None, description="Structural score (0-30, lower is better)")
    confidence_in_management: Optional[int] = Field(None, description="Management confidence score (0-30, lower is better)")


class FSAAddress(BaseModel):
    """Establishment address."""
    line1: Optional[str] = None
    line2: Optional[str] = None
    line3: Optional[str] = None
    line4: Optional[str] = None
    postcode: Optional[str] = None


class FSALocation(BaseModel):
    """Geographic coordinates."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FSAEstablishmentBase(BaseModel):
    """Base FSA establishment data."""
    fhrsid: int = Field(..., description="Food Hygiene Rating Scheme ID")
    business_name: str = Field(..., description="Business name")
    business_type: Optional[str] = None
    address: FSAAddress
    postcode: Optional[str] = None
    rating_value: Optional[str] = Field(None, description="Rating: 0-5, AwaitingInspection, Exempt")
    rating_date: Optional[datetime] = None
    scores: Optional[FSAScores] = None
    location: Optional[FSALocation] = None
    local_authority_name: Optional[str] = None


class FSAEstablishmentDetail(FSAEstablishmentBase):
    """Detailed FSA establishment data."""
    business_type_id: Optional[int] = None
    local_authority_code: Optional[int] = None
    local_authority_website: Optional[str] = None
    local_authority_email: Optional[str] = None
    scheme_type: Optional[str] = None
    new_rating_pending: Optional[str] = None
    right_to_reply: Optional[str] = None
    cached_at: Optional[datetime] = None


class FSASearchResponse(BaseModel):
    """Response for establishment search."""
    establishments: List[FSAEstablishmentBase]
    meta: dict = Field(default_factory=dict)


class FSAEstablishmentResponse(BaseModel):
    """Response for single establishment."""
    success: bool = True
    data: FSAEstablishmentDetail


class StandardResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[dict] = None
    error: Optional[dict] = None
    meta: Optional[dict] = None