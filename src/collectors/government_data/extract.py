import pandas as pd # type: ignore

def extract_food_balance(path):
    return pd.read_csv(path)

def extract_household_spending(path):
    return pd.read_csv(path)

def extract_nutrition_quality(path):
    return pd.read_csv(path)