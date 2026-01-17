from .extract import (
    extract_food_balance,
    extract_household_spending,
    extract_nutrition_quality,
)

from .transform import (
    transform_food_balance, 
    transform_household_spending, 
    transform_nutrition_quality,
)
from ...core.utils.validators import (
    validate_composite_key, 
    validate_year,
)
from .load import load_to_postgres
from ...database.postgres_connection import get_engine
 
engine = get_engine()

def run_food_balance_etl(engine):
    df = extract_food_balance("data/processed/food_balance.csv")
    df = transform_food_balance(df)
    validate_composite_key(df, ["food_label", "years", "unit"])
    load_to_postgres(df, "food_balance", engine)


def run_household_spending_etl(engine):
    df = extract_household_spending("data/processed/food_household_spending.csv")
    df = transform_household_spending(df)
    validate_composite_key(df, ["food_code", "years"])
    load_to_postgres(df, "food_household_spending", engine)

def run_nutrition_quality_etl(engine):
    df = extract_nutrition_quality("data/processed/food_nutrition_quality.csv")
    df = transform_nutrition_quality(df)
    validate_composite_key(df, ["food_name"])
    load_to_postgres(df, "food_nutrition_quality", engine)

def run_government_etl():
    engine = get_engine()

    print("Running food balance ETL...")
    run_food_balance_etl(engine)

    print("Running household spending ETL...")
    run_household_spending_etl(engine)

    print("Running nutrition quality ETL...")
    run_nutrition_quality_etl(engine)

    print("Government ETL pipeline completed successfully.")

if __name__ == "__main__":
    run_government_etl()