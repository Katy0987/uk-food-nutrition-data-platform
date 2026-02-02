"""
API routes for Open Food Facts product endpoints.
"""

import logging
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.repositories.off_repository import OFFRepository

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search")
async def search_products(
    query: Optional[str] = Query(None, description="Search terms"),
    category: Optional[str] = Query(None, description="Product category"),
    ecoscore: Optional[str] = Query(None, description="Eco-score grade (a-e)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Search for products by name, category, or eco-score.
    
    Returns products with eco-score and nutrition information.
    """
    start_time = time.time()
    
    try:
        # Validate ecoscore if provided
        if ecoscore and ecoscore.lower() not in ['a', 'b', 'c', 'd', 'e']:
            raise HTTPException(status_code=400, detail="Invalid ecoscore. Must be a, b, c, d, or e")
        
        repo = OFFRepository(db)
        results = repo.search_products(
            search_terms=query,
            category=category,
            ecoscore_grade=ecoscore.lower() if ecoscore else None,
            limit=limit
        )
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": results,
            "meta": {
                "count": len(results),
                "limit": limit,
                "filters": {
                    "query": query,
                    "category": category,
                    "ecoscore": ecoscore
                },
                "response_time_ms": round(process_time, 2)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/compare")
async def compare_products(
    barcodes: str = Query(..., description="Comma-separated barcodes (max 5)"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple products by barcode.
    
    Returns comparison data for eco-scores and nutrition across products.
    """
    start_time = time.time()
    
    try:
        # Parse barcodes
        barcode_list = [b.strip() for b in barcodes.split(",") if b.strip()]
        
        if not barcode_list:
            raise HTTPException(status_code=400, detail="No barcodes provided")
        
        if len(barcode_list) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 products can be compared")
        
        repo = OFFRepository(db)
        results = repo.compare_products(barcode_list)
        
        process_time = (time.time() - start_time) * 1000
        
        # Calculate comparison metrics
        valid_products = [p for p in results if "error" not in p]
        eco_scores = [
            p.get("ecoscore", {}).get("score")
            for p in valid_products
            if p.get("ecoscore", {}).get("score") is not None
        ]
        
        comparison = {}
        if eco_scores:
            comparison = {
                "best_ecoscore": max(eco_scores),
                "worst_ecoscore": min(eco_scores),
                "average_ecoscore": sum(eco_scores) / len(eco_scores)
            }
        
        return {
            "success": True,
            "data": results,
            "comparison": comparison,
            "meta": {
                "count": len(results),
                "valid_count": len(valid_products),
                "response_time_ms": round(process_time, 2)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compare products error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories/{category}/top-eco")
async def get_category_top_eco(
    category: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    min_score: int = Query(70, ge=0, le=100, description="Minimum eco-score"),
    db: Session = Depends(get_db)
):
    """
    Get top eco-friendly products in a category.
    
    Returns products with the highest eco-scores in the specified category.
    """
    start_time = time.time()
    
    try:
        repo = OFFRepository(db)
        results = repo.get_top_eco_products(
            category=category,
            limit=limit,
            min_ecoscore=min_score
        )
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": results,
            "meta": {
                "category": category,
                "count": len(results),
                "min_ecoscore": min_score,
                "response_time_ms": round(process_time, 2)
            }
        }
    except Exception as e:
        logger.error(f"Category top eco error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories/{category}/statistics")
async def get_category_statistics(
    category: str,
    db: Session = Depends(get_db)
):
    """
    Get eco-score statistics for a product category.
    
    Returns distribution and averages of eco-scores in the category.
    """
    start_time = time.time()
    
    try:
        repo = OFFRepository(db)
        stats = repo.get_category_statistics(category)
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": stats,
            "meta": {
                "response_time_ms": round(process_time, 2)
            }
        }
    except Exception as e:
        logger.error(f"Category statistics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{barcode}")
async def get_product(
    barcode: str,
    db: Session = Depends(get_db)
):
    """
    Get product information by barcode.
    
    Returns eco-score, nutri-score, and environmental impact data.
    """
    start_time = time.time()
    
    try:
        repo = OFFRepository(db)
        result = repo.get_product(barcode)
        
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": result,
            "meta": {
                "response_time_ms": round(process_time, 2)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
