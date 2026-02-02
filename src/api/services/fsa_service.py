"""
FSA Service Layer.
Provides business logic for Food Standards Agency data.
"""

import logging
from typing import Dict, List, Optional, Any

from collectors.external_apis.fsa_client import get_fsa_client, FSAAPIError

logger = logging.getLogger(__name__)


class FSAService:
    """Service for FSA establishment operations."""
    
    def __init__(self):
        self.client = get_fsa_client()
    
    def search_establishments_by_postcode(
        self,
        postcode: str,
        name: Optional[str] = None,
        business_type_id: Optional[int] = None,
        rating_key: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Search establishments by postcode with automatic local authority lookup.
        
        Args:
            postcode: Postcode to search
            name: Optional business name filter
            business_type_id: Optional business type filter
            rating_key: Optional rating filter
            page_number: Page number
            page_size: Results per page
            
        Returns:
            Dictionary with establishments and metadata
        """
        # Get local authority for the postcode
        local_authority = self.client.get_local_authority_from_postcode(postcode)
        
        local_authority_id = None
        if local_authority:
            local_authority_id = local_authority.get('LocalAuthorityId')
            logger.info(
                f"Found local authority {local_authority.get('Name')} "
                f"for postcode {postcode}"
            )
        
        # Search with local authority filter
        return self.client.search_establishments(
            postcode=postcode,
            name=name or '',  # Use empty string if no name provided
            local_authority_id=local_authority_id,
            business_type_id=business_type_id,
            rating_key=rating_key,
            page_number=page_number,
            page_size=page_size,
        )
    
    def search_establishments_by_area(
        self,
        local_authority_name: str,
        name: Optional[str] = None,
        postcode: Optional[str] = None,
        business_type_id: Optional[int] = None,
        rating_key: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Search establishments by local authority name.
        
        Args:
            local_authority_name: Name of local authority (e.g. 'Westminster')
            name: Optional business name filter
            postcode: Optional postcode filter
            business_type_id: Optional business type filter
            rating_key: Optional rating filter
            page_number: Page number
            page_size: Results per page
            
        Returns:
            Dictionary with establishments and metadata
        """
        # Look up local authority
        local_authority = self.client.get_local_authority_by_name(local_authority_name)
        
        if not local_authority:
            raise FSAAPIError(f"Local authority '{local_authority_name}' not found")
        
        local_authority_id = local_authority.get('LocalAuthorityId')
        
        return self.client.search_establishments(
            name=name,
            postcode=postcode,
            local_authority_id=local_authority_id,
            business_type_id=business_type_id,
            rating_key=rating_key,
            page_number=page_number,
            page_size=page_size,
        )
    
    def get_establishment_details(self, fhrsid: int) -> Dict[str, Any]:
        """
        Get full establishment details.
        
        Args:
            fhrsid: Food Hygiene Rating Scheme ID
            
        Returns:
            Establishment details
        """
        return self.client.get_establishment(fhrsid)
    
    def get_nearby_establishments(
        self,
        latitude: float,
        longitude: float,
        max_distance_miles: int = 1,
        business_type_id: Optional[int] = None,
        rating_key: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Find establishments near coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            max_distance_miles: Search radius in miles
            business_type_id: Optional business type filter
            rating_key: Optional rating filter
            page_number: Page number
            page_size: Results per page
            
        Returns:
            Dictionary with nearby establishments
        """
        return self.client.get_nearby_establishments(
            latitude=latitude,
            longitude=longitude,
            max_distance_limit=max_distance_miles,
            business_type_id=business_type_id,
            rating_key=rating_key,
            page_number=page_number,
            page_size=page_size,
        )
    
    def get_all_local_authorities(self) -> List[Dict[str, Any]]:
        """Get list of all local authorities."""
        return self.client.get_local_authorities()
    
    def get_all_business_types(self) -> List[Dict[str, Any]]:
        """Get list of all business types."""
        return self.client.get_business_types()


# Singleton instance
_fsa_service: Optional[FSAService] = None


def get_fsa_service() -> FSAService:
    """Get singleton FSA service instance."""
    global _fsa_service
    if _fsa_service is None:
        _fsa_service = FSAService()
    return _fsa_service