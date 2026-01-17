def validate_composite_key(df, keys):
    if df.duplicated(subset=keys).any():
        raise ValueError("Duplicate composite keys detected")

def validate_year(df):
    if not df["year"].between(2000, 2025).all():
        raise ValueError("Invalid year values")