"""
Scraped Data Validators
Validates daily bucket pattern structures for different scraper types.
"""

from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


# ============================================================================
# SUPERMARKET VALIDATORS (Sainsbury's, Asda)
# ============================================================================

def validate_supermarket_bucket(bucket_doc: Dict[str, Any]) -> bool:
    """
    Validates supermarket bucket structure.
    
    Expected structure:
    {
        "_id": "Fruit_and_Vegetable_2026-01-30",
        "store": "Sainsbury" or "Asda",
        "category": "Fruit and Vegetable",
        "date": "2026-01-30",
        "item_count": 50,
        "products": [
            {
                "name": "Product Name",
                "price": "£1.50" or 1.50,
                "product_url": "https://...",
                "scraped_at": "2026-01-30T12:00:00",
                "nutrition": {...}  # optional
            }
        ]
    }
    """
    # 1. Validate top-level required fields
    required_fields = ["_id", "store", "category", "date", "products"]
    for field in required_fields:
        if field not in bucket_doc:
            raise ValidationError(f"Supermarket bucket missing required field: '{field}'")
        if bucket_doc[field] is None:
            raise ValidationError(f"Supermarket bucket field '{field}' cannot be None")
    
    # 2. Validate store name
    valid_stores = ["Sainsbury", "Sainsburys", "Asda", "Morrisons", "Tesco", "Waitrose"]
    if bucket_doc["store"] not in valid_stores:
        logger.warning(f"Unknown store name: {bucket_doc['store']}")
    
    # 3. Validate date format
    date_str = bucket_doc["date"]
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")
    
    # 4. Validate products list
    products = bucket_doc.get("products", [])
    if not isinstance(products, list):
        raise ValidationError("'products' must be a list")
    
    if len(products) == 0:
        raise ValidationError("Bucket is empty. No products were scraped.")
    
    # 5. Validate item_count if present
    if "item_count" in bucket_doc:
        if bucket_doc["item_count"] != len(products):
            logger.warning(
                f"item_count ({bucket_doc['item_count']}) doesn't match "
                f"actual products length ({len(products)})"
            )
    
    # 6. Spot-check first product
    first_product = products[0]
    required_product_fields = ["name", "price"]
    
    for field in required_product_fields:
        if field not in first_product:
            raise ValidationError(f"Product missing required field: '{field}'")
    
    # 7. Validate product name
    if not first_product["name"] or len(first_product["name"].strip()) == 0:
        raise ValidationError("Product name cannot be empty")
    
    # 8. Validate price format
    price = first_product["price"]
    if isinstance(price, str):
        # Price as string (e.g., "£1.50")
        if not price.strip():
            raise ValidationError("Product price cannot be empty string")
    elif isinstance(price, (int, float)):
        # Price as number
        if price < 0:
            raise ValidationError(f"Product price cannot be negative: {price}")
    else:
        raise ValidationError(f"Invalid price type: {type(price)}")
    
    # 9. Validate optional fields
    if "product_url" in first_product:
        url = first_product["product_url"]
        if url and not url.startswith("http"):
            logger.warning(f"Product URL doesn't start with http: {url}")
    
    logger.info(
        f"✅ Supermarket bucket validated: {bucket_doc['store']} - "
        f"{bucket_doc['category']} ({len(products)} products)"
    )
    
    return True


# ============================================================================
# RESTAURANT VALIDATORS (McDonald's)
# ============================================================================

def validate_restaurant_bucket(bucket_doc: Dict[str, Any]) -> bool:
    """
    Validates restaurant bucket structure.
    
    Expected structure:
    {
        "_id": "Breakfast_2026-01-30",
        "metadata": {
            "date": "2026-01-30",
            "timestamp": "2026-01-30T12:00:00Z",
            "supermarket": "McDonalds",  # Note: uses "supermarket" field
            "category": "Breakfast"
        },
        "products": [
            {
                "name": "Egg McMuffin",
                "price": 3.49,
                "calories": 300,
                "is_limited_time": false,
                "url": "https://..."
            }
        ],
        "item_count": 12  # optional
    }
    """
    # 1. Validate top-level structure
    required_fields = ["_id", "metadata", "products"]
    for field in required_fields:
        if field not in bucket_doc:
            raise ValidationError(f"Restaurant bucket missing required field: '{field}'")
    
    # 2. Validate metadata
    metadata = bucket_doc.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValidationError("'metadata' must be a dictionary")
    
    required_metadata = ["date", "category"]
    for field in required_metadata:
        if field not in metadata:
            raise ValidationError(f"Metadata missing required field: '{field}'")
    
    # 3. Validate date format
    date_str = metadata["date"]
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")
    
    # 4. Validate products list
    products = bucket_doc.get("products", [])
    if not isinstance(products, list):
        raise ValidationError("'products' must be a list")
    
    if len(products) == 0:
        raise ValidationError("Bucket is empty. No products were scraped.")
    
    # 5. Spot-check first product
    first_product = products[0]
    required_product_fields = ["name", "price"]
    
    for field in required_product_fields:
        if field not in first_product:
            raise ValidationError(f"Product missing required field: '{field}'")
    
    # 6. Validate product name
    if not first_product["name"] or len(first_product["name"].strip()) == 0:
        raise ValidationError("Product name cannot be empty")
    
    # 7. Validate price
    price = first_product["price"]
    if not isinstance(price, (int, float)):
        raise ValidationError(f"Price must be a number, got: {type(price)}")
    if price < 0:
        raise ValidationError(f"Price cannot be negative: {price}")
    
    # 8. Validate calories if present
    if "calories" in first_product:
        calories = first_product["calories"]
    
    # Handle different types safely
        if isinstance(calories, str):
            try:
                calories_int = int(calories)
                if calories_int < 0:
                    logger.warning(f"Calories cannot be negative: {calories_int}")
            except ValueError:
                logger.warning(f"Calories is not a valid number: '{calories}'")
        elif isinstance(calories, int):
            if calories < 0:
                logger.warning(f"Calories cannot be negative: {calories}")
        elif isinstance(calories, float):
            logger.warning(f"Calories should be an integer, got float: {calories}")
        else:
            logger.warning(f"Calories has unexpected type: {type(calories)}")
    
    restaurant_name = metadata.get("supermarket", "Unknown")
    category = metadata.get("category", "Unknown")
    
    logger.info(
        f"✅ Restaurant bucket validated: {restaurant_name} - "
        f"{category} ({len(products)} products)"
    )
    
    return True


# ============================================================================
# GENERIC VALIDATORS
# ============================================================================

def validate_daily_bucket(bucket_doc: Dict[str, Any]) -> bool:
    """
    Generic validator that auto-detects the bucket type and validates accordingly.
    
    This is the main validator that should be imported and used.
    It will automatically detect whether it's a supermarket or restaurant bucket.
    """
    # Auto-detect bucket type based on structure
    
    # Check if it's a restaurant bucket (has metadata field)
    if "metadata" in bucket_doc and isinstance(bucket_doc["metadata"], dict):
        logger.debug("Detected restaurant bucket structure")
        return validate_restaurant_bucket(bucket_doc)
    
    # Check if it's a supermarket bucket (has store/category fields at top level)
    elif "store" in bucket_doc and "category" in bucket_doc:
        logger.debug("Detected supermarket bucket structure")
        return validate_supermarket_bucket(bucket_doc)
    
    # Unknown structure - try to validate as generic
    else:
        logger.warning("Unknown bucket structure, performing basic validation")
        return validate_basic_bucket(bucket_doc)


def validate_basic_bucket(bucket_doc: Dict[str, Any]) -> bool:
    """
    Basic validation for any bucket structure.
    Checks only the most essential fields.
    """
    # 1. Must have _id
    if "_id" not in bucket_doc:
        raise ValidationError("Bucket missing required field: '_id'")
    
    # 2. Must have products
    if "products" not in bucket_doc:
        raise ValidationError("Bucket missing required field: 'products'")
    
    products = bucket_doc["products"]
    
    # 3. Products must be a list
    if not isinstance(products, list):
        raise ValidationError("'products' must be a list")
    
    # 4. Products must not be empty
    if len(products) == 0:
        raise ValidationError("Bucket is empty. No products were scraped.")
    
    # 5. First product must have name
    first_product = products[0]
    if "name" not in first_product:
        raise ValidationError("Product missing required field: 'name'")
    
    if not first_product["name"] or len(first_product["name"].strip()) == 0:
        raise ValidationError("Product name cannot be empty")
    
    logger.info(f"✅ Basic bucket validated: {bucket_doc['_id']} ({len(products)} products)")
    
    return True


# ============================================================================
# BATCH VALIDATORS
# ============================================================================

def validate_multiple_buckets(buckets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate multiple buckets and return summary statistics.
    
    Returns:
        {
            "total": 10,
            "valid": 8,
            "invalid": 2,
            "errors": [...]
        }
    """
    results = {
        "total": len(buckets),
        "valid": 0,
        "invalid": 0,
        "errors": []
    }
    
    for idx, bucket in enumerate(buckets):
        try:
            validate_daily_bucket(bucket)
            results["valid"] += 1
        except ValidationError as e:
            results["invalid"] += 1
            results["errors"].append({
                "index": idx,
                "bucket_id": bucket.get("_id", "unknown"),
                "error": str(e)
            })
        except Exception as e:
            results["invalid"] += 1
            results["errors"].append({
                "index": idx,
                "bucket_id": bucket.get("_id", "unknown"),
                "error": f"Unexpected error: {str(e)}"
            })
    
    return results


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_validation_summary(bucket_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of a bucket without raising errors.
    Useful for debugging.
    """
    summary = {
        "_id": bucket_doc.get("_id", "missing"),
        "has_products": "products" in bucket_doc,
        "product_count": len(bucket_doc.get("products", [])),
        "structure_type": "unknown"
    }
    
    # Detect type
    if "metadata" in bucket_doc:
        summary["structure_type"] = "restaurant"
        summary["category"] = bucket_doc.get("metadata", {}).get("category", "unknown")
    elif "store" in bucket_doc:
        summary["structure_type"] = "supermarket"
        summary["store"] = bucket_doc.get("store", "unknown")
        summary["category"] = bucket_doc.get("category", "unknown")
    
    # Check first product
    products = bucket_doc.get("products", [])
    if products:
        first = products[0]
        summary["sample_product"] = {
            "name": first.get("name", "missing")[:50],
            "has_price": "price" in first,
            "has_url": "url" in first or "product_url" in first
        }
    
    return summary