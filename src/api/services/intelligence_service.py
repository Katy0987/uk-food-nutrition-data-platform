"""
Intelligence Service - Aggregates FSA and OFF data with district insights.
This is the "Brain" that combines hygiene ratings with eco-scores.
"""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from api.repositories.fsa_repository import FSARepository
from api.repositories.off_repository import OFFRepository
from src.api.services.fsa_service import get_fsa_service

logger = logging.getLogger(__name__)


class IntelligenceService:
    """Service for aggregated intelligence and insights."""

    def __init__(self, db: Session):
        """
        Initialize intelligence service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.fsa_repo = FSARepository(db)
        self.off_repo = OFFRepository(db)
        # ADD THIS LINE:
        self.fsa_service = get_fsa_service()

    # Now you can use self.fsa_service in your methods
    # For example, if you need to fetch fresh data from FSA API:
    
    def get_district_intelligence(self, postcode: str) -> Dict[str, Any]:
        """
        Get comprehensive district intelligence by postcode.
        Combines FSA hygiene data with eco-score insights.
        
        Args:
            postcode: UK postcode
            
        Returns:
            District intelligence data
        """
        logger.info(f"Generating district intelligence for {postcode}")
        
        # OPTION 1: Use repository (from database - EXISTING)
        hygiene_stats = self.fsa_repo.get_statistics_by_postcode(postcode)
        establishments = self.fsa_repo.search_establishments(
            postcode=postcode,
            limit=50
        )
        
        # OPTION 2: Use FSA service to fetch fresh data from API (NEW)
        # Uncomment this if you want fresh data from the API instead of database:
        # try:
        #     fresh_data = self.fsa_service.search_establishments_by_postcode(
        #         postcode=postcode,
        #         page_size=50
        #     )
        #     establishments = fresh_data.get('establishments', [])
        # except Exception as e:
        #     logger.warning(f"Failed to fetch fresh FSA data: {e}, using database")
        #     establishments = self.fsa_repo.search_establishments(
        #         postcode=postcode,
        #         limit=50
        #     )
        
        # Get eco-friendly products (sample from database)
        eco_products = self.off_repo.get_top_eco_products(limit=10)
        
        # Calculate insights
        insights = self._calculate_insights(hygiene_stats, eco_products)
        
        return {
            "postcode": postcode,
            "hygiene_stats": {
                "total_establishments": hygiene_stats.get("total_establishments", 0),
                "rating_distribution": hygiene_stats.get("rating_distribution", {}),
                "average_hygiene_score": hygiene_stats.get("average_hygiene_score"),
                "top_rated_count": hygiene_stats.get("rating_distribution", {}).get("5", 0)
            },
            "establishments_sample": establishments[:10],  # Top 10
            "eco_insights": {
                "top_sustainable_products": eco_products[:5],
                "average_ecoscore": self._calculate_average_ecoscore(eco_products),
                "eco_friendly_count": len([p for p in eco_products if p.get("ecoscore", {}).get("grade") in ["a", "b"]])
            },
            "insights": insights,
            "recommendations": self._generate_recommendations(hygiene_stats, eco_products)
        }

logger = logging.getLogger(__name__)


class IntelligenceService:
    """Service for aggregated intelligence and insights."""

    def __init__(self, db: Session):
        """
        Initialize intelligence service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.fsa_repo = FSARepository(db)
        self.off_repo = OFFRepository(db)

    def get_district_intelligence(self, postcode: str) -> Dict[str, Any]:
        """
        Get comprehensive district intelligence by postcode.
        Combines FSA hygiene data with eco-score insights.
        
        Args:
            postcode: UK postcode
            
        Returns:
            District intelligence data
        """
        logger.info(f"Generating district intelligence for {postcode}")
        
        # Get FSA hygiene statistics
        hygiene_stats = self.fsa_repo.get_statistics_by_postcode(postcode)
        
        # Get establishments in area
        establishments = self.fsa_repo.search_establishments(
            postcode=postcode,
            limit=50
        )
        
        # Get eco-friendly products (sample from database)
        eco_products = self.off_repo.get_top_eco_products(limit=10)
        
        # Calculate insights
        insights = self._calculate_insights(hygiene_stats, eco_products)
        
        return {
            "postcode": postcode,
            "hygiene_stats": {
                "total_establishments": hygiene_stats.get("total_establishments", 0),
                "rating_distribution": hygiene_stats.get("rating_distribution", {}),
                "average_hygiene_score": hygiene_stats.get("average_hygiene_score"),
                "top_rated_count": hygiene_stats.get("rating_distribution", {}).get("5", 0)
            },
            "establishments_sample": establishments[:10],  # Top 10
            "eco_insights": {
                "top_sustainable_products": eco_products[:5],
                "average_ecoscore": self._calculate_average_ecoscore(eco_products),
                "eco_friendly_count": len([p for p in eco_products if p.get("ecoscore", {}).get("grade") in ["a", "b"]])
            },
            "insights": insights,
            "recommendations": self._generate_recommendations(hygiene_stats, eco_products)
        }

    def get_establishment_with_nearby_products(
        self,
        fhrsid: int,
        product_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get establishment details with nearby sustainable product options.
        
        Args:
            fhrsid: Establishment ID
            product_category: Filter products by category
            
        Returns:
            Establishment with product recommendations
        """
        # Get establishment
        establishment = self.fsa_repo.get_establishment(fhrsid)
        
        if not establishment:
            return {"error": "Establishment not found"}
        
        # Get eco-friendly products
        if product_category:
            products = self.off_repo.search_products(
                category=product_category,
                ecoscore_grade="a",
                limit=10
            )
        else:
            products = self.off_repo.get_top_eco_products(limit=10)
        
        return {
            "establishment": establishment,
            "sustainable_alternatives": products,
            "sustainability_score": self._calculate_sustainability_score(
                establishment,
                products
            )
        }

    def compare_establishments_and_products(
        self,
        fhrsids: List[int],
        barcodes: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple establishments and products.
        
        Args:
            fhrsids: List of establishment IDs
            barcodes: List of product barcodes
            
        Returns:
            Comparison data
        """
        # Get establishments
        establishments = []
        for fhrsid in fhrsids[:5]:  # Max 5
            est = self.fsa_repo.get_establishment(fhrsid)
            if est:
                establishments.append(est)
        
        # Get products
        products = self.off_repo.compare_products(barcodes[:5])  # Max 5
        
        return {
            "establishments": {
                "data": establishments,
                "comparison": self._compare_hygiene_ratings(establishments)
            },
            "products": {
                "data": products,
                "comparison": self._compare_eco_scores(products)
            },
            "overall_insights": {
                "best_hygiene": self._find_best_hygiene(establishments),
                "best_ecoscore": self._find_best_ecoscore(products)
            }
        }

    def get_category_insights(self, category: str) -> Dict[str, Any]:
        """
        Get insights for a product category.
        
        Args:
            category: Product category
            
        Returns:
            Category insights
        """
        # Get category statistics
        stats = self.off_repo.get_category_statistics(category)
        
        # Get top products
        top_products = self.off_repo.get_top_eco_products(
            category=category,
            limit=10
        )
        
        return {
            "category": category,
            "statistics": stats,
            "top_products": top_products,
            "insights": {
                "eco_friendly_percentage": self._calculate_eco_percentage(stats),
                "average_ecoscore_grade": self._score_to_grade(stats.get("average_ecoscore"))
            }
        }

    # Helper methods
    
    def _calculate_insights(
        self,
        hygiene_stats: Dict[str, Any],
        eco_products: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights from data."""
        insights = []
        
        total_est = hygiene_stats.get("total_establishments", 0)
        if total_est > 0:
            rating_dist = hygiene_stats.get("rating_distribution", {})
            top_rated = rating_dist.get("5", 0)
            percentage = (top_rated / total_est) * 100
            
            if percentage > 70:
                insights.append(f"Excellent hygiene standards: {percentage:.0f}% of establishments have 5-star ratings")
            elif percentage > 50:
                insights.append(f"Good hygiene standards: {percentage:.0f}% of establishments have 5-star ratings")
            else:
                insights.append(f"Hygiene standards vary: Only {percentage:.0f}% have 5-star ratings")
        
        # Eco insights
        eco_friendly = len([p for p in eco_products if p.get("ecoscore", {}).get("grade") in ["a", "b"]])
        if eco_friendly > 7:
            insights.append("Strong availability of eco-friendly products")
        elif eco_friendly > 4:
            insights.append("Moderate availability of eco-friendly products")
        else:
            insights.append("Limited eco-friendly product options")
        
        return insights

    def _generate_recommendations(
        self,
        hygiene_stats: Dict[str, Any],
        eco_products: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        # Hygiene recommendations
        total = hygiene_stats.get("total_establishments", 0)
        if total > 0:
            rating_dist = hygiene_stats.get("rating_distribution", {})
            low_rated = rating_dist.get("1", 0) + rating_dist.get("2", 0)
            
            if low_rated > 0:
                recommendations.append("Check hygiene ratings before dining out")
            
            recommendations.append("Prefer establishments with 4-5 star ratings")
        
        # Eco recommendations
        if eco_products:
            recommendations.append("Look for products with A or B eco-scores")
            recommendations.append("Choose locally sourced products to reduce carbon footprint")
        
        return recommendations

    def _calculate_average_ecoscore(self, products: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate average eco-score."""
        scores = [
            p.get("ecoscore", {}).get("score")
            for p in products
            if p.get("ecoscore", {}).get("score") is not None
        ]
        
        if scores:
            return sum(scores) / len(scores)
        return None

    def _calculate_sustainability_score(
        self,
        establishment: Dict[str, Any],
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall sustainability score."""
        # Hygiene component (0-100)
        rating = establishment.get("rating_value", "0")
        try:
            hygiene_score = int(rating) * 20  # Convert 0-5 to 0-100
        except ValueError:
            hygiene_score = 0
        
        # Eco component (0-100)
        avg_ecoscore = self._calculate_average_ecoscore(products) or 0
        
        # Combined score
        overall = (hygiene_score * 0.5) + (avg_ecoscore * 0.5)
        
        return {
            "overall": round(overall, 1),
            "hygiene_component": hygiene_score,
            "eco_component": round(avg_ecoscore, 1),
            "grade": self._score_to_grade(overall)
        }

    def _compare_hygiene_ratings(self, establishments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare hygiene ratings."""
        if not establishments:
            return {}
        
        ratings = []
        for est in establishments:
            try:
                rating = int(est.get("rating_value", "0"))
                ratings.append(rating)
            except ValueError:
                ratings.append(0)
        
        return {
            "highest_rating": max(ratings) if ratings else 0,
            "lowest_rating": min(ratings) if ratings else 0,
            "average_rating": sum(ratings) / len(ratings) if ratings else 0
        }

    def _compare_eco_scores(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare eco-scores."""
        if not products:
            return {}
        
        scores = [
            p.get("ecoscore", {}).get("score")
            for p in products
            if p.get("ecoscore", {}).get("score") is not None
        ]
        
        if not scores:
            return {}
        
        return {
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "average_score": sum(scores) / len(scores)
        }

    def _find_best_hygiene(self, establishments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find establishment with best hygiene rating."""
        if not establishments:
            return None
        
        best = max(
            establishments,
            key=lambda x: int(x.get("rating_value", "0")) if x.get("rating_value", "0").isdigit() else 0
        )
        return best

    def _find_best_ecoscore(self, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find product with best eco-score."""
        if not products:
            return None
        
        valid_products = [
            p for p in products
            if p.get("ecoscore", {}).get("score") is not None
        ]
        
        if not valid_products:
            return None
        
        best = max(
            valid_products,
            key=lambda x: x.get("ecoscore", {}).get("score", 0)
        )
        return best

    def _calculate_eco_percentage(self, stats: Dict[str, Any]) -> float:
        """Calculate percentage of eco-friendly products."""
        dist = stats.get("ecoscore_distribution", {})
        total = stats.get("total_products", 0)
        
        if total == 0:
            return 0.0
        
        eco_friendly = dist.get("a", 0) + dist.get("b", 0)
        return (eco_friendly / total) * 100

    def _score_to_grade(self, score: Optional[float]) -> str:
        """Convert numerical score to letter grade."""
        if score is None:
            return "unknown"
        
        if score >= 80:
            return "a"
        elif score >= 60:
            return "b"
        elif score >= 40:
            return "c"
        elif score >= 20:
            return "d"
        else:
            return "e"