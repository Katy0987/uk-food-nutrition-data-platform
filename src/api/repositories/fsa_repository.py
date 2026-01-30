"""
Repository for FSA (Food Standards Agency) data with caching.
Handles data access, caching, and persistence for establishment data.
"""

import logging
import hashlib
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from api.config import settings
from api.database.redis_client import get_redis_client
from collectors.external_apis.fsa_client import get_fsa_client, FSAAPIError
from core.models.establishment import Establishment

logger = logging.getLogger(__name__)


class FSARepository:
    """Repository for FSA establishment data."""

    def __init__(self, db: Session, cache_enabled: bool = None):
        """
        Initialize repository.
        
        Args:
            db: Database session
            cache_enabled: Override cache setting (default from config)
        """
        self.db = db
        self.redis = get_redis_client()
        self.fsa_client = get_fsa_client()
        self.cache_enabled = cache_enabled if cache_enabled is not None else settings.enable_caching

    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"fsa:{prefix}:{params_hash}"

    def _cache_get(self, key: str) -> Optional[Any]:
        """Get from cache if enabled."""
        if not self.cache_enabled:
            return None
        return self.redis.get(key)

    def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set to cache if enabled."""
        if not self.cache_enabled:
            return
        ttl = ttl or settings.cache_ttl_establishment
        self.redis.set(key, value, ttl=ttl)

    def get_establishment(self, fhrsid: int, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get establishment by FHRSID.
        
        Args:
            fhrsid: Food Hygiene Rating Scheme ID
            force_refresh: Force API refresh
            
        Returns:
            Establishment data or None if not found
        """
        cache_key = f"fsa:establishment:{fhrsid}"

        # Check cache first
        if not force_refresh:
            cached = self._cache_get(cache_key)
            if cached:
                logger.debug(f"Cache hit for establishment {fhrsid}")
                return cached

        # Check database
        if not force_refresh:
            db_record = self.db.query(Establishment).filter(
                Establishment.fhrsid == fhrsid
            ).first()
            
            if db_record and not db_record.is_stale():
                data = db_record.to_dict()
                self._cache_set(cache_key, data)
                logger.debug(f"Database hit for establishment {fhrsid}")
                return data

        # Fetch from API
        try:
            logger.info(f"Fetching establishment {fhrsid} from FSA API")
            api_data = self.fsa_client.get_establishment(fhrsid)
            
            # Transform and save
            establishment_data = self._transform_fsa_data(api_data)
            self._save_establishment(establishment_data)
            
            # Cache result
            self._cache_set(cache_key, establishment_data)
            
            return establishment_data
            
        except FSAAPIError as e:
            logger.error(f"FSA API error for {fhrsid}: {str(e)}")
            return None

    def search_establishments(
        self,
        name: Optional[str] = None,
        postcode: Optional[str] = None,
        rating_value: Optional[str] = None,
        limit: int = 20,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search establishments.
        
        Args:
            name: Business name filter
            postcode: Postcode filter
            rating_value: Rating filter
            limit: Maximum results
            force_refresh: Force API refresh
            
        Returns:
            List of establishment data
        """
        # Generate cache key
        cache_key = self._get_cache_key(
            "search",
            name=name,
            postcode=postcode,
            rating_value=rating_value,
            limit=limit
        )

        # Check cache
        if not force_refresh:
            cached = self._cache_get(cache_key)
            if cached:
                logger.debug("Cache hit for search")
                return cached

        # Try database first for performance
        if not force_refresh:
            query = self.db.query(Establishment)
            
            if name:
                query = query.filter(Establishment.business_name.ilike(f"%{name}%"))
            if postcode:
                clean_postcode = postcode.replace(" ", "")
                query = query.filter(Establishment.postcode.ilike(f"%{clean_postcode}%"))
            if rating_value:
                query = query.filter(Establishment.rating_value == rating_value)
            
            results = query.limit(limit).all()
            
            if results:
                data = [r.to_dict() for r in results]
                self._cache_set(cache_key, data, ttl=settings.cache_ttl_search)
                logger.debug(f"Database hit for search, found {len(data)} results")
                return data

        # Fetch from API
        try:
            logger.info("Fetching search results from FSA API")
            api_response = self.fsa_client.search_establishments(
                name=name,
                postcode=postcode,
                rating_key=rating_value,
                page_size=limit
            )
            
            establishments = api_response.get("establishments", [])
            
            # Transform and save
            results = []
            for est_data in establishments:
                transformed = self._transform_fsa_data(est_data)
                self._save_establishment(transformed)
                results.append(transformed)
            
            # Cache results
            self._cache_set(cache_key, results, ttl=settings.cache_ttl_search)
            
            return results
            
        except FSAAPIError as e:
            logger.error(f"FSA API search error: {str(e)}")
            return []

    def get_nearby_establishments(
        self,
        latitude: float,
        longitude: float,
        radius_miles: int = 1,
        limit: int = 20,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Find establishments near coordinates.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            radius_miles: Search radius in miles
            limit: Maximum results
            force_refresh: Force API refresh
            
        Returns:
            List of nearby establishments
        """
        try:
            logger.info(f"Searching nearby establishments at {latitude},{longitude}")
            api_response = self.fsa_client.get_nearby_establishments(
                latitude=latitude,
                longitude=longitude,
                max_distance_limit=radius_miles,
                page_size=limit
            )
            
            establishments = api_response.get("establishments", [])
            
            results = []
            for est_data in establishments:
                transformed = self._transform_fsa_data(est_data)
                self._save_establishment(transformed)
                results.append(transformed)
            
            return results
            
        except FSAAPIError as e:
            logger.error(f"FSA API nearby search error: {str(e)}")
            return []

    def get_statistics_by_postcode(self, postcode: str) -> Dict[str, Any]:
        """
        Get hygiene statistics for a postcode area.
        
        Args:
            postcode: Postcode prefix (e.g., "SW1A")
            
        Returns:
            Statistics dictionary
        """
        # Clean postcode
        clean_postcode = postcode.replace(" ", "")[:4]  # Get first 4 chars
        
        # Query database
        query = self.db.query(Establishment).filter(
            Establishment.postcode.ilike(f"{clean_postcode}%")
        )
        
        total = query.count()
        
        if total == 0:
            return {
                "postcode": postcode,
                "total_establishments": 0,
                "rating_distribution": {},
                "average_hygiene_score": None
            }
        
        # Rating distribution
        rating_dist = {}
        for rating in ["5", "4", "3", "2", "1", "0"]:
            count = query.filter(Establishment.rating_value == rating).count()
            if count > 0:
                rating_dist[rating] = count
        
        # Average scores
        avg_hygiene = self.db.query(
            func.avg(Establishment.hygiene_score)
        ).filter(
            Establishment.postcode.ilike(f"{clean_postcode}%"),
            Establishment.hygiene_score.isnot(None)
        ).scalar()
        
        return {
            "postcode": postcode,
            "total_establishments": total,
            "rating_distribution": rating_dist,
            "average_hygiene_score": float(avg_hygiene) if avg_hygiene else None
        }

    def _transform_fsa_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform FSA API data to standard format."""
        return {
            "fhrsid": api_data.get("FHRSID"),
            "business_name": api_data.get("BusinessName"),
            "business_type": api_data.get("BusinessType"),
            "business_type_id": api_data.get("BusinessTypeID"),
            "address": {
                "line1": api_data.get("AddressLine1"),
                "line2": api_data.get("AddressLine2"),
                "line3": api_data.get("AddressLine3"),
                "line4": api_data.get("AddressLine4"),
                "postcode": api_data.get("PostCode")
            },
            "postcode": api_data.get("PostCode"),
            "rating_value": api_data.get("RatingValue"),
            "rating_date": api_data.get("RatingDate"),
            "rating_key": api_data.get("RatingKey"),
            "scores": {
                "hygiene": api_data.get("scores", {}).get("Hygiene"),
                "structural": api_data.get("scores", {}).get("Structural"),
                "confidence_in_management": api_data.get("scores", {}).get("ConfidenceInManagement")
            },
            "location": {
                "latitude": api_data.get("geocode", {}).get("latitude"),
                "longitude": api_data.get("geocode", {}).get("longitude")
            },
            "local_authority_code": api_data.get("LocalAuthorityCode"),
            "local_authority_name": api_data.get("LocalAuthorityName"),
            "local_authority_website": api_data.get("LocalAuthorityWebSite"),
            "local_authority_email": api_data.get("LocalAuthorityEmailAddress"),
            "scheme_type": api_data.get("SchemeType"),
            "new_rating_pending": api_data.get("NewRatingPending"),
            "right_to_reply": api_data.get("RightToReply"),
            "cached_at": datetime.utcnow().isoformat()
        }

    def _save_establishment(self, data: Dict[str, Any]) -> Establishment:
        """Save or update establishment in database."""
        fhrsid = data.get("fhrsid")
        
        # Check if exists
        existing = self.db.query(Establishment).filter(
            Establishment.fhrsid == fhrsid
        ).first()
        
        if existing:
            # Update
            for key, value in data.items():
                if key == "address":
                    existing.address_line_1 = value.get("line1")
                    existing.address_line_2 = value.get("line2")
                    existing.address_line_3 = value.get("line3")
                    existing.address_line_4 = value.get("line4")
                elif key == "scores":
                    existing.hygiene_score = value.get("hygiene")
                    existing.structural_score = value.get("structural")
                    existing.confidence_in_management_score = value.get("confidence_in_management")
                elif key == "location":
                    existing.latitude = value.get("latitude")
                    existing.longitude = value.get("longitude")
                elif hasattr(existing, key):
                    setattr(existing, key, value)
            
            existing.updated_at = datetime.utcnow()
            establishment = existing
        else:
            # Create new
            establishment = Establishment(
                fhrsid=fhrsid,
                business_name=data.get("business_name"),
                business_type=data.get("business_type"),
                business_type_id=data.get("business_type_id"),
                address_line_1=data.get("address", {}).get("line1"),
                address_line_2=data.get("address", {}).get("line2"),
                address_line_3=data.get("address", {}).get("line3"),
                address_line_4=data.get("address", {}).get("line4"),
                postcode=data.get("postcode"),
                rating_value=data.get("rating_value"),
                rating_key=data.get("rating_key"),
                hygiene_score=data.get("scores", {}).get("hygiene"),
                structural_score=data.get("scores", {}).get("structural"),
                confidence_in_management_score=data.get("scores", {}).get("confidence_in_management"),
                latitude=data.get("location", {}).get("latitude"),
                longitude=data.get("location", {}).get("longitude"),
                local_authority_code=data.get("local_authority_code"),
                local_authority_name=data.get("local_authority_name"),
                local_authority_website=data.get("local_authority_website"),
                local_authority_email=data.get("local_authority_email"),
                scheme_type=data.get("scheme_type"),
                new_rating_pending=data.get("new_rating_pending"),
                right_to_reply=data.get("right_to_reply"),
                cached_at=datetime.utcnow()
            )
            self.db.add(establishment)
        
        self.db.commit()
        self.db.refresh(establishment)
        
        return establishment