from sqlalchemy import create_engine # type: ignore

def load_to_postgres(df, table_name, engine):
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )