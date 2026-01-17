def transform_food_balance(df):
    df.columns = df.columns.str.lower()
    df["years"] = df["years"].astype(int)
    df["amount"] = df["amount"].astype(float)
    return df

def transform_household_spending(df):
    df.columns = df.columns.str.lower()
    df["years"] = df["years"].astype(int)
    df["food_code"] = df["food_code"].astype(str)
    return df

def transform_nutrition_quality(df):
    df.columns = df.columns.str.lower()
    nutrition_cols = [
        "energy_kcal", "fat_g", "saturates_g", "carbohydrate_g",
        "sugars_g", "fibre_g", "protein_g", "salt_g"
    ]
    df[nutrition_cols] = df[nutrition_cols].astype(float)
    return df