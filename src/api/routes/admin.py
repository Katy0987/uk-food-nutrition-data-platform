"""
API routes for admin/metrics endpoints.
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.database.session import get_db, get_db_stats
from api.database.redis_client import get_redis_client
from core.models.establishment import Establishment
from core.models.product_eco import ProductEco

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """
    Get system metrics and statistics.
    
    Returns performance metrics, cache statistics, and data counts.
    """
    try:
        # Database metrics
        establishment_count = db.query(func.count(Establishment.id)).scalar()
        product_count = db.query(func.count(ProductEco.id)).scalar()
        db_pool_stats = get_db_stats()
        
        # Redis metrics
        redis = get_redis_client()
        redis_stats = redis.get_stats()
        
        # Recent establishments
        recent_establishments = db.query(func.count(Establishment.id)).filter(
            Establishment.cached_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).scalar()
        
        # Recent products
        recent_products = db.query(func.count(ProductEco.id)).filter(
            ProductEco.cached_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).scalar()
        
        return {
            "success": True,
            "data": {
                "database": {
                    "establishments_total": establishment_count,
                    "products_total": product_count,
                    "establishments_today": recent_establishments,
                    "products_today": recent_products,
                    "pool_stats": db_pool_stats
                },
                "cache": {
                    "hit_rate": redis_stats.get("hit_rate", 0),
                    "memory_used": redis_stats.get("used_memory_human", "0B"),
                    "total_commands": redis_stats.get("total_commands_processed", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear all cached data.
    
    WARNING: This will clear the entire Redis cache.
    """
    try:
        redis = get_redis_client()
        redis.flush()
        
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health/detailed")
async def detailed_health(db: Session = Depends(get_db)):
    """
    Detailed health check with component status.
    
    Returns health status of all system components.
    """
    try:
        from api.database.session import check_connection
        
        # Check PostgreSQL
        postgres_ok = check_connection()
        
        # Check Redis
        redis = get_redis_client()
        redis_ok = redis.check_connection()
        
        # Check database queries
        try:
            db.query(func.count(Establishment.id)).scalar()
            db_query_ok = True
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            db_query_ok = False
        
        all_ok = postgres_ok and redis_ok and db_query_ok
        
        return {
            "status": "healthy" if all_ok else "degraded",
            "components": {
                "postgresql": {
                    "status": "up" if postgres_ok else "down",
                    "connection": "ok" if postgres_ok else "failed"
                },
                "redis": {
                    "status": "up" if redis_ok else "down",
                    "connection": "ok" if redis_ok else "failed"
                },
                "database_queries": {
                    "status": "ok" if db_query_ok else "error"
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/stats/summary")
async def get_summary_stats(db: Session = Depends(get_db)):
    """
    Get summary statistics across all data sources.
    
    Returns aggregated statistics for quick overview.
    """
    try:
        # Establishment stats
        total_establishments = db.query(func.count(Establishment.id)).scalar()
        
        rating_dist = {}
        for rating in ["5", "4", "3", "2", "1", "0"]:
            count = db.query(func.count(Establishment.id)).filter(
                Establishment.rating_value == rating
            ).scalar()
            if count > 0:
                rating_dist[rating] = count
        
        # Product stats
        total_products = db.query(func.count(ProductEco.id)).scalar()
        
        ecoscore_dist = {}
        for grade in ["a", "b", "c", "d", "e"]:
            count = db.query(func.count(ProductEco.id)).filter(
                ProductEco.ecoscore_grade == grade
            ).scalar()
            if count > 0:
                ecoscore_dist[grade] = count
        
        # Average scores
        avg_hygiene = db.query(func.avg(Establishment.hygiene_score)).filter(
            Establishment.hygiene_score.isnot(None)
        ).scalar()
        
        avg_ecoscore = db.query(func.avg(ProductEco.ecoscore_score)).filter(
            ProductEco.ecoscore_score.isnot(None)
        ).scalar()
        
        return {
            "success": True,
            "data": {
                "establishments": {
                    "total": total_establishments,
                    "rating_distribution": rating_dist,
                    "average_hygiene_score": float(avg_hygiene) if avg_hygiene else None
                },
                "products": {
                    "total": total_products,
                    "ecoscore_distribution": ecoscore_dist,
                    "average_ecoscore": float(avg_ecoscore) if avg_ecoscore else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Summary stats error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")