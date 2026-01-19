def validate_daily_bucket(bucket_doc: dict):
    """
    Validates the new Bucket Pattern structure for daily scrapes.
    Checks the main document and the list of products within it.
    """
    # 1. Validate Top-Level Metadata
    required_metadata = ["_id", "source", "date", "products"]

    for field in required_metadata:
        if field not in bucket_doc or bucket_doc[field] is None:
            raise ValueError(f"Bucket missing required metadata: {field}")

    # 2. Validate the Products List
    products = bucket_doc.get("products", [])
    
    if not isinstance(products, list):
        raise ValueError("'products' must be a list of items")

    if len(products) == 0:
        raise ValueError("Bucket is empty. No products were scraped.")

    # 3. Spot-check the first item to ensure parsing is working
    first_item = products[0]
    required_item_fields = ["name", "price"]
    
    for field in required_item_fields:
        if field not in first_item:
            raise ValueError(f"Product items are missing required field: {field}")

    return True