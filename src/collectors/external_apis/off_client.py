"""
Open Food Facts (OFF) API Client.
Handles HTTP requests to the Open Food Facts API for product eco-scores.
Documentation: https://wiki.openfoodfacts.org/API
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


class OFFAPIError(Exception):
    """Custom exception for OFF API errors."""
    pass


class OFFClient:
    """
    Client for Open Food Facts API.
    
    Provides methods to:
    - Get product by barcode
    - Search products by name, category, brand
    - Get products with best eco-scores
    - Get products by category
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize OFF API client.
        
        Args:
            base_url: OFF API base URL (default from settings)
            timeout: Request timeout in seconds (default from settings)
            user_agent: User agent string (default from settings)
            max_retries: Maximum number of retries (default from settings)
        """
        self.base_url = base_url or settings.off_api_base_url
        self.timeout = timeout or settings.off_api_timeout
        self.user_agent = user_agent or settings.off_api_user_agent
        self.max_retries = max_retries or settings.off_api_max_retries
        
        # OFF API headers
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        
        # Create HTTP client
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
        )
        
        logger.info(f"OFF Client initialized with base URL: {self.base_url}")

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
            OFFAPIError: If request fails after retries
        """
        try:
            logger.debug(f"OFF API Request: {method} {endpoint} with params: {params}")
            
            response = self.client.request(
                method=method,
                url=endpoint,
                params=params,
                **kwargs
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"OFF API Response: Status {response.status_code}")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OFF API HTTP error: {e.response.status_code} - {e.response.text}")
            raise OFFAPIError(
                f"OFF API request failed: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"OFF API request error: {str(e)}")
            raise OFFAPIError(f"OFF API request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"OFF API JSON decode error: {str(e)}")
            raise OFFAPIError(f"Invalid JSON response from OFF API: {str(e)}")

    def get_product(self, barcode: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get product by barcode.
        
        Args:
            barcode: Product barcode (EAN-13, UPC, etc.)
            fields: Specific fields to return (optional)
            
        Returns:
            Product data dictionary
        """
        endpoint = f"/api/v2/product/{barcode}"
        
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
            
        response = self._request("GET", endpoint, params=params)
        
        # OFF returns status in response body
        if response.get("status") != 1:
            raise OFFAPIError(f"Product not found: {barcode}")
            
        return response.get("product", {})

    def search_products(
        self,
        search_terms: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        ecoscore_grade: Optional[str] = None,
        nutriscore_grade: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "ecoscore_score",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search products with filters.
        
        Args:
            search_terms: Text search query
            category: Category filter (e.g., "beverages")
            brand: Brand filter
            ecoscore_grade: Eco-score filter (a, b, c, d, e)
            nutriscore_grade: Nutri-score filter (a, b, c, d, e)
            page: Page number (starts at 1)
            page_size: Results per page (max 100)
            sort_by: Sort field (default: ecoscore_score)
            fields: Specific fields to return
            
        Returns:
            Dictionary with products and metadata
        """
        endpoint = "/cgi/search.pl"
        
        params = {
            "json": "1",
            "page": page,
            "page_size": min(page_size, 100),
            "sort_by": sort_by,
        }
        
        if search_terms:
            params["search_terms"] = search_terms
        if category:
            params["tagtype_0"] = "categories"
            params["tag_contains_0"] = "contains"
            params["tag_0"] = category
        if brand:
            params["tagtype_1"] = "brands"
            params["tag_contains_1"] = "contains"
            params["tag_1"] = brand
        if ecoscore_grade:
            params["tagtype_2"] = "ecoscore"
            params["tag_contains_2"] = "contains"
            params["tag_2"] = ecoscore_grade.lower()
        if nutriscore_grade:
            params["tagtype_3"] = "nutrition_grades"
            params["tag_contains_3"] = "contains"
            params["tag_3"] = nutriscore_grade.lower()
        if fields:
            params["fields"] = ",".join(fields)
            
        return self._request("GET", endpoint, params=params)

    def get_top_eco_products(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        min_ecoscore: int = 70,
    ) -> List[Dict[str, Any]]:
        """
        Get products with best eco-scores.
        
        Args:
            category: Filter by category (optional)
            limit: Maximum number of products
            min_ecoscore: Minimum eco-score (0-100)
            
        Returns:
            List of product dictionaries
        """
        response = self.search_products(
            category=category,
            page_size=limit,
            sort_by="ecoscore_score",
        )
        
        products = response.get("products", [])
        
        # Filter by minimum eco-score
        filtered = [
            p for p in products
            if p.get("ecoscore_score", 0) >= min_ecoscore
        ]
        
        return filtered[:limit]

    def get_products_by_category(
        self,
        category: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get products by category.
        
        Args:
            category: Category name
            page: Page number
            page_size: Results per page
            
        Returns:
            Dictionary with products and metadata
        """
        return self.search_products(
            category=category,
            page=page,
            page_size=page_size,
        )

    def compare_products(
        self,
        barcodes: List[str],
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get multiple products for comparison.
        
        Args:
            barcodes: List of product barcodes (max 5)
            fields: Specific fields to return
            
        Returns:
            List of product dictionaries
        """
        if len(barcodes) > 5:
            raise OFFAPIError("Maximum 5 products can be compared at once")
            
        products = []
        for barcode in barcodes:
            try:
                product = self.get_product(barcode, fields=fields)
                products.append(product)
            except OFFAPIError as e:
                logger.warning(f"Failed to get product {barcode}: {str(e)}")
                products.append({
                    "code": barcode,
                    "error": str(e),
                    "status": "not_found",
                })
                
        return products

    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get list of all product categories.
        
        Returns:
            List of category dictionaries
        """
        endpoint = "/categories.json"
        response = self._request("GET", endpoint)
        return response.get("tags", [])

    def get_brands(self, page: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of brands.
        
        Args:
            page: Page number
            page_size: Results per page
            
        Returns:
            List of brand dictionaries
        """
        endpoint = "/brands.json"
        params = {
            "page": page,
            "page_size": page_size,
        }
        response = self._request("GET", endpoint, params=params)
        return response.get("tags", [])

    def get_product_fields(self) -> List[str]:
        """
        Get list of available product fields.
        Useful for optimizing API requests.
        
        Returns:
            List of field names
        """
        # Common fields for eco-score analysis
        return [
            "code",
            "product_name",
            "generic_name",
            "brands",
            "brands_tags",
            "categories",
            "categories_tags",
            "ecoscore_grade",
            "ecoscore_score",
            "ecoscore_data",
            "nutriscore_grade",
            "nutriscore_score",
            "nutrition_grades",
            "carbon_footprint_100g",
            "carbon_footprint_from_known_ingredients_100g",
            "manufacturing_places",
            "manufacturing_places_tags",
            "origins",
            "origins_tags",
            "packaging",
            "packaging_tags",
            "labels",
            "labels_tags",
            "quantity",
            "serving_size",
            "image_url",
            "image_small_url",
            "image_ingredients_url",
            "image_nutrition_url",
            "energy_100g",
            "fat_100g",
            "saturated-fat_100g",
            "carbohydrates_100g",
            "sugars_100g",
            "fiber_100g",
            "proteins_100g",
            "salt_100g",
            "ingredients_text",
            "countries",
            "countries_tags",
            "stores",
            "stores_tags",
            "completeness",
        ]


# Singleton instance for convenience
_off_client: Optional[OFFClient] = None


def get_off_client() -> OFFClient:
    """
    Get singleton OFF client instance.
    
    Returns:
        OFF client instance
    """
    global _off_client
    if _off_client is None:
        _off_client = OFFClient()
    return _off_client