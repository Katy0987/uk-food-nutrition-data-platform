from sqlalchemy import create_engine, text

def load_to_postgres(df, table_name, engine):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name}"))
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )