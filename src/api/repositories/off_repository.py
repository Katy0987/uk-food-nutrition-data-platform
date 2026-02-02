"""
Repository for Open Food Facts data with caching.
Handles data access, caching, and persistence for product eco-score data.
"""

import logging
import hashlib
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from api.config import settings
from api.database.redis_client import get_redis_client
from collectors.external_apis.off_client import get_off_client, OFFAPIError
from core.models.product_eco import ProductEco

logger = logging.getLogger(__name__)


class OFFRepository:
    """Repository for Open Food Facts product data."""

    def __init__(self, db: Session, cache_enabled: bool = None):
        """
        Initialize repository.
        
        Args:
            db: Database session
            cache_enabled: Override cache setting
        """
        self.db = db
        self.redis = get_redis_client()
        self.off_client = get_off_client()
        self.cache_enabled = cache_enabled if cache_enabled is not None else settings.enable_caching

    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"off:{prefix}:{params_hash}"

    def _cache_get(self, key: str) -> Optional[Any]:
        """Get from cache if enabled."""
        if not self.cache_enabled:
            return None
        return self.redis.get(key)

    def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set to cache if enabled."""
        if not self.cache_enabled:
            return
        ttl = ttl or settings.cache_ttl_product
        self.redis.set(key, value, ttl=ttl)

    def get_product(self, barcode: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get product by barcode.
        
        Args:
            barcode: Product barcode
            force_refresh: Force API refresh
            
        Returns:
            Product data or None if not found
        """
        cache_key = f"off:product:{barcode}"

        # Check cache
        if not force_refresh:
            cached = self._cache_get(cache_key)
            if cached:
                logger.debug(f"Cache hit for product {barcode}")
                return cached

        # Check database
        if not force_refresh:
            db_record = self.db.query(ProductEco).filter(
                ProductEco.barcode == barcode
            ).first()
            
            if db_record and not db_record.is_stale():
                data = db_record.to_dict()
                self._cache_set(cache_key, data)
                logger.debug(f"Database hit for product {barcode}")
                return data

        # Fetch from API
        try:
            logger.info(f"Fetching product {barcode} from OFF API")
            api_data = self.off_client.get_product(barcode)
            
            # Transform and save
            product_data = self._transform_off_data(api_data, barcode)
            self._save_product(product_data)
            
            # Cache result
            self._cache_set(cache_key, product_data)
            
            return product_data
            
        except OFFAPIError as e:
            logger.error(f"OFF API error for {barcode}: {str(e)}")
            return None

    def search_products(
        self,
        search_terms: Optional[str] = None,
        category: Optional[str] = None,
        ecoscore_grade: Optional[str] = None,
        limit: int = 20,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search products.
        
        Args:
            search_terms: Text search
            category: Category filter
            ecoscore_grade: Eco-score filter
            limit: Maximum results
            force_refresh: Force API refresh
            
        Returns:
            List of product data
        """
        # Generate cache key
        cache_key = self._get_cache_key(
            "search",
            search_terms=search_terms,
            category=category,
            ecoscore_grade=ecoscore_grade,
            limit=limit
        )

        # Check cache
        if not force_refresh:
            cached = self._cache_get(cache_key)
            if cached:
                logger.debug("Cache hit for product search")
                return cached

        # Try database first
        if not force_refresh and not search_terms:
            query = self.db.query(ProductEco)
            
            if category:
                query = query.filter(ProductEco.categories.ilike(f"%{category}%"))
            if ecoscore_grade:
                query = query.filter(ProductEco.ecoscore_grade == ecoscore_grade.lower())
            
            results = query.order_by(desc(ProductEco.ecoscore_score)).limit(limit).all()
            
            if results:
                data = [r.to_dict() for r in results]
                self._cache_set(cache_key, data, ttl=settings.cache_ttl_search)
                logger.debug(f"Database hit for search, found {len(data)} results")
                return data

        # Fetch from API
        try:
            logger.info("Fetching search results from OFF API")
            api_response = self.off_client.search_products(
                search_terms=search_terms,
                category=category,
                ecoscore_grade=ecoscore_grade,
                page_size=limit,
                sort_by="ecoscore_score"
            )
            
            products = api_response.get("products", [])
            
            results = []
            for prod_data in products:
                barcode = prod_data.get("code", "")
                if barcode:
                    transformed = self._transform_off_data(prod_data, barcode)
                    self._save_product(transformed)
                    results.append(transformed)
            
            # Cache results
            self._cache_set(cache_key, results, ttl=settings.cache_ttl_search)
            
            return results
            
        except OFFAPIError as e:
            logger.error(f"OFF API search error: {str(e)}")
            return []

    def compare_products(self, barcodes: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple products for comparison.
        
        Args:
            barcodes: List of barcodes (max 5)
            
        Returns:
            List of product data
        """
        if len(barcodes) > 5:
            barcodes = barcodes[:5]
        
        results = []
        for barcode in barcodes:
            product = self.get_product(barcode)
            if product:
                results.append(product)
            else:
                results.append({
                    "barcode": barcode,
                    "error": "Product not found",
                    "status": "not_found"
                })
        
        return results

    def get_top_eco_products(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        min_ecoscore: int = 70
    ) -> List[Dict[str, Any]]:
        """
        Get products with best eco-scores.
        
        Args:
            category: Category filter
            limit: Maximum results
            min_ecoscore: Minimum eco-score
            
        Returns:
            List of top products
        """
        query = self.db.query(ProductEco).filter(
            ProductEco.ecoscore_score >= min_ecoscore,
            ProductEco.ecoscore_score.isnot(None)
        )
        
        if category:
            query = query.filter(ProductEco.categories.ilike(f"%{category}%"))
        
        results = query.order_by(
            desc(ProductEco.ecoscore_score)
        ).limit(limit).all()
        
        return [r.to_dict() for r in results]

    def get_category_statistics(self, category: str) -> Dict[str, Any]:
        """
        Get eco-score statistics for a category.
        
        Args:
            category: Product category
            
        Returns:
            Statistics dictionary
        """
        from sqlalchemy import func
        
        query = self.db.query(ProductEco).filter(
            ProductEco.categories.ilike(f"%{category}%")
        )
        
        total = query.count()
        
        if total == 0:
            return {
                "category": category,
                "total_products": 0,
                "ecoscore_distribution": {},
                "average_ecoscore": None
            }
        
        # Eco-score distribution
        ecoscore_dist = {}
        for grade in ["a", "b", "c", "d", "e"]:
            count = query.filter(ProductEco.ecoscore_grade == grade).count()
            if count > 0:
                ecoscore_dist[grade] = count
        
        # Average eco-score
        avg_score = self.db.query(
            func.avg(ProductEco.ecoscore_score)
        ).filter(
            ProductEco.categories.ilike(f"%{category}%"),
            ProductEco.ecoscore_score.isnot(None)
        ).scalar()
        
        return {
            "category": category,
            "total_products": total,
            "ecoscore_distribution": ecoscore_dist,
            "average_ecoscore": float(avg_score) if avg_score else None
        }

    def _transform_off_data(self, api_data: Dict[str, Any], barcode: str) -> Dict[str, Any]:
        """Transform OFF API data to standard format."""
        return {
            "barcode": barcode,
            "product_name": api_data.get("product_name"),
            "generic_name": api_data.get("generic_name"),
            "brands": api_data.get("brands"),
            "categories": api_data.get("categories"),
            "main_category": api_data.get("main_category"),
            "ecoscore": {
                "grade": api_data.get("ecoscore_grade"),
                "score": api_data.get("ecoscore_score"),
                "data": api_data.get("ecoscore_data")
            },
            "nutriscore": {
                "grade": api_data.get("nutriscore_grade"),
                "score": api_data.get("nutriscore_score")
            },
            "environmental_impact": {
                "carbon_footprint_100g": api_data.get("carbon_footprint_100g"),
                "manufacturing_impact": api_data.get("manufacturing_impact"),
                "packaging_impact": api_data.get("packaging_impact"),
                "transportation_impact": api_data.get("transportation_impact")
            },
            "packaging": api_data.get("packaging"),
            "manufacturing_places": api_data.get("manufacturing_places"),
            "origins": api_data.get("origins"),
            "labels": api_data.get("labels"),
            "quantity": api_data.get("quantity"),
            "serving_size": api_data.get("serving_size"),
            "images": {
                "url": api_data.get("image_url"),
                "small": api_data.get("image_small_url"),
                "ingredients": api_data.get("image_ingredients_url"),
                "nutrition": api_data.get("image_nutrition_url")
            },
            "nutrition_per_100g": {
                "energy": api_data.get("energy_100g"),
                "fat": api_data.get("fat_100g"),
                "saturated_fat": api_data.get("saturated-fat_100g"),
                "carbohydrates": api_data.get("carbohydrates_100g"),
                "sugars": api_data.get("sugars_100g"),
                "fiber": api_data.get("fiber_100g"),
                "proteins": api_data.get("proteins_100g"),
                "salt": api_data.get("salt_100g")
            },
            "ingredients": {
                "text": api_data.get("ingredients_text"),
                "count": api_data.get("ingredients_count")
            },
            "completeness": api_data.get("completeness"),
            "cached_at": datetime.utcnow().isoformat()
        }

    def _save_product(self, data: Dict[str, Any]) -> ProductEco:
        """Save or update product in database."""
        barcode = data.get("barcode")
        
        # Check if exists
        existing = self.db.query(ProductEco).filter(
            ProductEco.barcode == barcode
        ).first()
        
        if existing:
            # Update
            existing.product_name = data.get("product_name")
            existing.generic_name = data.get("generic_name")
            existing.brands = data.get("brands")
            existing.categories = data.get("categories")
            existing.main_category = data.get("main_category")
            existing.ecoscore_grade = data.get("ecoscore", {}).get("grade")
            existing.ecoscore_score = data.get("ecoscore", {}).get("score")
            existing.ecoscore_data = data.get("ecoscore", {}).get("data")
            existing.nutriscore_grade = data.get("nutriscore", {}).get("grade")
            existing.nutriscore_score = data.get("nutriscore", {}).get("score")
            existing.carbon_footprint_100g = data.get("environmental_impact", {}).get("carbon_footprint_100g")
            existing.manufacturing_impact = data.get("environmental_impact", {}).get("manufacturing_impact")
            existing.packaging_impact = data.get("environmental_impact", {}).get("packaging_impact")
            existing.packaging = data.get("packaging")
            existing.manufacturing_places = data.get("manufacturing_places")
            existing.origins = data.get("origins")
            existing.labels = data.get("labels")
            existing.quantity = data.get("quantity")
            existing.serving_size = data.get("serving_size")
            existing.image_url = data.get("images", {}).get("url")
            existing.image_small_url = data.get("images", {}).get("small")
            existing.ingredients_text = data.get("ingredients", {}).get("text")
            existing.completeness = data.get("completeness")
            existing.updated_at = datetime.utcnow()
            product = existing
        else:
            # Create new
            product = ProductEco(
                barcode=barcode,
                product_name=data.get("product_name"),
                generic_name=data.get("generic_name"),
                brands=data.get("brands"),
                categories=data.get("categories"),
                main_category=data.get("main_category"),
                ecoscore_grade=data.get("ecoscore", {}).get("grade"),
                ecoscore_score=data.get("ecoscore", {}).get("score"),
                ecoscore_data=data.get("ecoscore", {}).get("data"),
                nutriscore_grade=data.get("nutriscore", {}).get("grade"),
                nutriscore_score=data.get("nutriscore", {}).get("score"),
                carbon_footprint_100g=data.get("environmental_impact", {}).get("carbon_footprint_100g"),
                manufacturing_impact=data.get("environmental_impact", {}).get("manufacturing_impact"),
                packaging_impact=data.get("environmental_impact", {}).get("packaging_impact"),
                packaging=data.get("packaging"),
                manufacturing_places=data.get("manufacturing_places"),
                origins=data.get("origins"),
                labels=data.get("labels"),
                quantity=data.get("quantity"),
                serving_size=data.get("serving_size"),
                image_url=data.get("images", {}).get("url"),
                image_small_url=data.get("images", {}).get("small"),
                ingredients_text=data.get("ingredients", {}).get("text"),
                completeness=data.get("completeness"),
                cached_at=datetime.utcnow()
            )
            self.db.add(product)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product