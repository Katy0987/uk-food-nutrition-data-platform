"""Populate database with sample data from external APIs"""
from api.database.session import SessionLocal
from api.repositories.fsa_repository import FSARepository
from api.repositories.off_repository import OFFRepository

print("🌱 Populating database with real data from external APIs...")
print("This will take 1-2 minutes...\n")

db = SessionLocal()

try:
    fsa_repo = FSARepository(db)
    off_repo = OFFRepository(db)
    
    # Fetch establishments from London
    print("📍 Fetching establishments from London areas...")
    fsa_repo.search_establishments(postcode="SW1A", limit=20)
    print("   ✅ SW1A area: 20 establishments")
    
    fsa_repo.search_establishments(postcode="EC1A", limit=20)
    print("   ✅ EC1A area: 20 establishments")
    
    fsa_repo.search_establishments(postcode="W1A", limit=20)
    print("   ✅ W1A area: 20 establishments")
    
    # Fetch products
    print("\n🥤 Fetching products from Open Food Facts...")
    off_repo.search_products(category="beverages", limit=20)
    print("   ✅ Beverages: 20 products")
    
    off_repo.search_products(category="snacks", limit=20)
    print("   ✅ Snacks: 20 products")
    
    off_repo.search_products(ecoscore_grade="a", limit=20)
    print("   ✅ Eco-friendly (A grade): 20 products")
    
    print("\n✅ Database populated successfully!")
    print("\nYou can now test with real data:")
    print('  curl "http://localhost:8000/api/v1/establishments/search?postcode=SW1A&limit=5"')
    print('  curl "http://localhost:8000/api/v1/products/search?category=beverages&limit=5"')
    
finally:
    db.close()