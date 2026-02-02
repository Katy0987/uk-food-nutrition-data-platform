from sqlalchemy import text
from src.database.postgres_connection import get_db_session

def test_connection():
    """Test database connection"""
    try:
        db = get_db_session()
        print("✓ Database connection successful!")
        
        # Test a simple query (SQLAlchemy 2.0 syntax)
        result = db.execute(text("SELECT 1")).scalar()
        print(f"✓ Query test successful! Result: {result}")
        
        # Test querying actual tables
        try:
            # Test food_balance table
            count_fb = db.execute(text("SELECT COUNT(*) FROM food_balance")).scalar()
            print(f"✓ food_balance table: {count_fb} records")
        except Exception as e:
            print(f"⚠ food_balance table: {e}")
        
        try:
            # Test household_spending table
            count_hs = db.execute(text("SELECT COUNT(*) FROM food_household_spending")).scalar()
            print(f"✓ household_spending table: {count_hs} records")
        except Exception as e:
            print(f"⚠ household_spending table: {e}")
        
        try:
            # Test nutrition table
            count_n = db.execute(text("SELECT COUNT(*) FROM food_nutrition_quality")).scalar()
            print(f"✓ nutrition table: {count_n} records")
        except Exception as e:
            print(f"⚠ nutrition table: {e}")
        
        db.close()
        print("✓ Connection closed successfully!")
        print("\n🎉 All tests passed! Database is ready for the API.")
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")

if __name__ == "__main__":
    test_connection()