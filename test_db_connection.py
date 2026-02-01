from src.database.postgres_connection import get_db_session

def test_connection():
    """Test database connection"""
    try:
        db = get_db_session()
        print("✓ Database connection successful!")
        
        # Test a simple query
        result = db.execute("SELECT 1").scalar()
        print(f"✓ Query test successful! Result: {result}")
        
        db.close()
        print("✓ Connection closed successfully!")
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")

if __name__ == "__main__":
    test_connection()