from extract.read_processed_csv import extract_food_balance
from validate.structured_validation import validate_composite_key
from load.load_postgres import load_to_postgres
from db.postgres_connection import get_engine

engine = get_engine()

df = extract_food_balance("data/processed/food_balance_clean.csv")

validate_composite_key(df, ["food_code", "year"])

load_to_postgres(df, "food_balance", engine)
