"""
Food Standards Agency (FSA) API Client.
Handles HTTP requests to the FSA Food Hygiene Rating Scheme API v2.
Documentation: https://api.ratings.food.gov.uk/help
"""

import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from api.config import settings

logger = logging.getLogger(__name__)


class FSAAPIError(Exception):
    """Custom exception for FSA API errors."""
    pass


class FSAClient:
    """
    Client for Food Standards Agency API v2.
    
    Provides methods to:
    - Search establishments by name, address, postcode
    - Get establishment details by FHRSID
    - Search nearby establishments by coordinates
    - List local authorities
    - Get business types
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize FSA API client.
        
        Args:
            base_url: FSA API base URL (default from settings)
            api_version: API version (default from settings)
            timeout: Request timeout in seconds (default from settings)
            max_retries: Maximum number of retries (default from settings)
        """
        self.base_url = base_url or settings.fsa_api_base_url
        self.api_version = api_version or settings.fsa_api_version
        self.timeout = timeout or settings.fsa_api_timeout
        self.max_retries = max_retries or settings.fsa_api_max_retries
        
        # FSA API requires specific headers
        self.headers = {
            "x-api-version": "2",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        # Build full API URL
        self.api_url = urljoin(self.base_url, self.api_version)
        
        # Create HTTP client
        self.client = httpx.Client(
            base_url=self.api_url,
            headers=self.headers,
            timeout=self.timeout,
        )
        
        logger.info(f"FSA Client initialized with base URL: {self.api_url}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            **kwargs: Additional request arguments
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            FSAAPIError: If request fails after retries
        """
        try:
            logger.debug(f"FSA API Request: {method} {endpoint} with params: {params}")
            
            response = self.client.request(
                method=method,
                url=endpoint,
                params=params,
                **kwargs
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"FSA API Response: Status {response.status_code}")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"FSA API HTTP error: {e.response.status_code} - {e.response.text}")
            raise FSAAPIError(
                f"FSA API request failed: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"FSA API request error: {str(e)}")
            raise FSAAPIError(f"FSA API request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"FSA API JSON decode error: {str(e)}")
            raise FSAAPIError(f"Invalid JSON response from FSA API: {str(e)}")

    def search_establishments(
        self,
        name: Optional[str] = None,
        address: Optional[str] = None,
        postcode: Optional[str] = None,
        local_authority_id: Optional[int] = None,
        business_type_id: Optional[int] = None,
        rating_key: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for establishments.
        
        Args:
            name: Business name to search
            address: Address to search
            postcode: Postcode to search
            local_authority_id: Filter by local authority
            business_type_id: Filter by business type
            rating_key: Filter by rating (0-5, AwaitingInspection, Exempt)
            page_number: Page number (starts at 1)
            page_size: Results per page (max 5000)
            
        Returns:
            Dictionary with establishments and metadata
        """
        params = {
            "pageNumber": page_number,
            "pageSize": min(page_size, 5000),  # FSA max is 5000
        }
        
        if name:
            params["name"] = name
        if address:
            params["address"] = address
        if postcode:
            params["postCode"] = postcode.replace(" ", "")  # Remove spaces
        if local_authority_id:
            params["localAuthorityId"] = local_authority_id
        if business_type_id:
            params["businessTypeId"] = business_type_id
        if rating_key:
            params["ratingKey"] = rating_key
            
        return self._request("GET", "/Establishments", params=params)

    def get_establishment(self, fhrsid: int) -> Dict[str, Any]:
        """
        Get establishment details by FHRSID.
        
        Args:
            fhrsid: Food Hygiene Rating Scheme ID
            
        Returns:
            Establishment details dictionary
        """
        return self._request("GET", f"/Establishments/{fhrsid}")

    def get_nearby_establishments(
        self,
        latitude: float,
        longitude: float,
        max_distance_limit: int = 1,  # miles
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
            max_distance_limit: Search radius in miles (default 1)
            business_type_id: Filter by business type
            rating_key: Filter by rating
            page_number: Page number
            page_size: Results per page
            
        Returns:
            Dictionary with nearby establishments
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "maxDistanceLimit": max_distance_limit,
            "pageNumber": page_number,
            "pageSize": min(page_size, 5000),
        }
        
        if business_type_id:
            params["businessTypeId"] = business_type_id
        if rating_key:
            params["ratingKey"] = rating_key
            
        return self._request("GET", "/Establishments", params=params)

    def get_local_authorities(self) -> List[Dict[str, Any]]:
        """
        Get list of all local authorities.
        
        Returns:
            List of local authority dictionaries
        """
        response = self._request("GET", "/Authorities")
        return response.get("authorities", [])

    def get_local_authority(self, local_authority_id: int) -> Dict[str, Any]:
        """
        Get details for specific local authority.
        
        Args:
            local_authority_id: Local authority ID
            
        Returns:
            Local authority details
        """
        return self._request("GET", f"/Authorities/{local_authority_id}")

    def get_business_types(self) -> List[Dict[str, Any]]:
        """
        Get list of all business types.
        
        Returns:
            List of business type dictionaries
        """
        response = self._request("GET", "/BusinessTypes")
        return response.get("businessTypes", [])

    def get_ratings(self) -> List[Dict[str, Any]]:
        """
        Get list of all rating schemes.
        
        Returns:
            List of rating scheme dictionaries
        """
        response = self._request("GET", "/Ratings")
        return response.get("ratings", [])

    def get_scheme_types(self) -> List[Dict[str, Any]]:
        """
        Get list of all scheme types.
        
        Returns:
            List of scheme type dictionaries
        """
        response = self._request("GET", "/SchemeTypes")
        return response.get("schemeTypes", [])


# Singleton instance for convenience
_fsa_client: Optional[FSAClient] = None


def get_fsa_client() -> FSAClient:
    """
    Get singleton FSA client instance.
    
    Returns:
        FSA client instance
    """
    global _fsa_client
    if _fsa_client is None:
        _fsa_client = FSAClient()
    return _fsa_client