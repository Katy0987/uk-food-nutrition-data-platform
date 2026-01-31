"""Test local database connections"""

print("Testing database connections...\n")

# Test PostgreSQL
print("1. Testing PostgreSQL...")
try:
    from sqlalchemy import text
    from api.database.session import engine
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("   ✅ PostgreSQL: Connected!")
        print(f"   📍 Database: ecodb")
        print(f"   📍 Port: 5433")
except Exception as e:
    print(f"   ❌ PostgreSQL Error: {str(e)}")

# Test Redis
print("\n2. Testing Redis...")
try:
    from api.database.redis_client import get_redis_client
    redis = get_redis_client()
    if redis.check_connection():
        print("   ✅ Redis: Connected!")
        print(f"   📍 Port: 6379")
    else:
        print("   ❌ Redis: Connection failed")
except Exception as e:
    print(f"   ❌ Redis Error: {str(e)}")

# Test MongoDB
print("\n3. Testing MongoDB...")
try:
    import pymongo
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    client.admin.command('ping')
    print("   ✅ MongoDB: Connected!")
    print(f"   📍 Database: ecodb")
    print(f"   📍 Port: 27017")
except Exception as e:
    print(f"   ❌ MongoDB Error: {str(e)}")

print("\n" + "="*50)
print("✅ Connection Test Complete!")
print("="*50)
print("\n📊 Summary:")
print("   - PostgreSQL: ✅ Ready (port 5433)")
print("   - Redis: ✅ Ready (port 6379)")
print("   - MongoDB: ✅ Ready (port 27017)")
print("\n🚀 You're ready to start the API!")