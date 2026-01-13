import pandas as pd

def extract_food_balance(path):
    return pd.read_csv(path)

def extract_household_spending(path):
    return pd.read_csv(path)
