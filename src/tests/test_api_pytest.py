"""
Pytest test suite for EcoAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.database.session import Base, get_db

# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite:///./test_ecoapi.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data

    def test_health(self):
        """Test health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_status(self):
        """Test detailed status."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestEstablishmentEndpoints:
    """Test establishment endpoints."""

    def test_search_establishments_no_params(self):
        """Test search without parameters."""
        response = client.get("/api/v1/establishments/search")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_search_establishments_with_postcode(self):
        """Test search with postcode."""
        response = client.get(
            "/api/v1/establishments/search",
            params={"postcode": "SW1A", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_nearby_establishments(self):
        """Test nearby establishments search."""
        response = client.get(
            "/api/v1/establishments/nearby",
            params={"lat": 51.5074, "lon": -0.1278, "radius": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_nearby_establishments_invalid_coords(self):
        """Test nearby with invalid coordinates."""
        response = client.get(
            "/api/v1/establishments/nearby",
            params={"lat": 999, "lon": -0.1278}
        )
        assert response.status_code == 422  # Validation error


class TestProductEndpoints:
    """Test product endpoints."""

    def test_search_products_no_params(self):
        """Test product search without parameters."""
        response = client.get("/api/v1/products/search")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_search_products_with_category(self):
        """Test product search with category."""
        response = client.get(
            "/api/v1/products/search",
            params={"category": "beverages", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_search_products_invalid_ecoscore(self):
        """Test product search with invalid eco-score."""
        response = client.get(
            "/api/v1/products/search",
            params={"ecoscore": "z"}
        )
        assert response.status_code == 400

    def test_category_top_eco(self):
        """Test category top eco-friendly products."""
        response = client.get("/api/v1/products/categories/beverages/top-eco")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestIntelligenceEndpoints:
    """Test intelligence endpoints."""

    def test_district_intelligence(self):
        """Test district intelligence."""
        response = client.get("/api/v1/intelligence/district/SW1A1AA")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_category_insights(self):
        """Test category insights."""
        response = client.get("/api/v1/intelligence/category/beverages/insights")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAdminEndpoints:
    """Test admin endpoints."""

    def test_get_metrics(self):
        """Test metrics endpoint."""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "database" in data["data"]

    def test_detailed_health(self):
        """Test detailed health check."""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_summary_stats(self):
        """Test summary statistics."""
        response = client.get("/api/v1/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestPerformance:
    """Test API performance."""

    def test_response_time_establishments(self):
        """Test establishment search response time."""
        import time
        start = time.time()
        response = client.get("/api/v1/establishments/search", params={"limit": 20})
        duration = (time.time() - start) * 1000
        
        assert response.status_code == 200
        # Should be under 500ms
        assert duration < 500, f"Response took {duration}ms, expected < 500ms"

    def test_response_time_products(self):
        """Test product search response time."""
        import time
        start = time.time()
        response = client.get("/api/v1/products/search", params={"limit": 20})
        duration = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert duration < 500, f"Response took {duration}ms, expected < 500ms"
