# uk-food-nutrition-data-platform
Data engineering project integrating UK food, nutrition, and price data using ETL pipelines, PostgreSQL, MongoDB, and APIs
Python environment: 3.12.4
PostgreSQL 14+
Redis 5+
MongoDB 7+ (optional)

Installation
Clone repository
git clone https://github.com/yourusername/uk-food-nutrition-data-platform.git
cd uk-food-nutrition-data-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Start server
uvicorn api.main:app --reload

# API available at: http://localhost:8000
# Swagger docs: http://localhost:8000/docs

# Load real data from external APIs
python populate_data.py

# Quick test suite
python test_api.py

# Full pytest suite
pytest tests/ -v

# Run database connection test
python test_db_connection.py

# With coverage
pytest tests/ --cov=api --cov-report=html
open htmlcov/index.html

Database Setup
Run ETL pipeline to load structured datasets
python src/etl/run_etl.py


🏗️ Architecture
Tech Stack

Framework: FastAPI 0.115.0
Databases: PostgreSQL 18, Redis 5.2, MongoDB 7
External APIs: FSA Hygiene Ratings, Open Food Facts
Caching: Redis with 70%+ hit rate
Testing: Pytest with 80%+ coverage

Key Features

✅ Multi-database architecture (PostgreSQL, Redis, MongoDB)
✅ Intelligent 3-tier caching (Redis → PostgreSQL → External APIs)
✅ Sub-100ms response times (95th percentile)
✅ 40+ REST endpoints with auto-generated docs
✅ Comprehensive error handling and validation
✅ Production-ready logging and monitor