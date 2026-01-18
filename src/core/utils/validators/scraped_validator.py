def validate_scraped_food_item(doc: dict):
    required_fields = ["source", "item_name", "scraped_at"]

    for field in required_fields:
        if field not in doc or doc[field] is None:
            raise ValueError(f"Missing required field: {field}")

    if "price" in doc and doc["price"] is not None:
        if doc["price"].get("value", 0) < 0:
            raise ValueError("Price cannot be negative")

    return True