"""
API routes for intelligence endpoints (aggregated insights).
"""

import logging
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.services.intelligence_service import IntelligenceService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/district/{postcode}")
async def get_district_intelligence(
    postcode: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive district intelligence by postcode.
    
    Combines FSA hygiene data with eco-score insights to provide
    a complete picture of sustainability and food safety in the area.
    """
    start_time = time.time()
    
    try:
        service = IntelligenceService(db)
        result = service.get_district_intelligence(postcode)
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": result,
            "meta": {
                "response_time_ms": round(process_time, 2)
            }
        }
    except Exception as e:
        logger.error(f"District intelligence error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/establishment/{fhrsid}/products")
async def get_establishment_with_products(
    fhrsid: int,
    category: str = Query(None, description="Product category filter"),
    db: Session = Depends(get_db)
):
    """
    Get establishment with nearby sustainable product options.
    
    Returns establishment details along with recommended eco-friendly products.
    """
    start_time = time.time()
    
    try:
        service = IntelligenceService(db)
        result = service.get_establishment_with_nearby_products(
            fhrsid=fhrsid,
            product_category=category
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
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
        logger.error(f"Establishment products error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/compare")
async def compare_establishments_and_products(
    fhrsids: str = Query(None, description="Comma-separated establishment IDs (max 5)"),
    barcodes: str = Query(None, description="Comma-separated product barcodes (max 5)"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple establishments and products.
    
    Provides side-by-side comparison of hygiene ratings and eco-scores.
    """
    start_time = time.time()
    
    try:
        # Parse IDs
        fhrsid_list = []
        if fhrsids:
            fhrsid_list = [int(f.strip()) for f in fhrsids.split(",") if f.strip()]
        
        barcode_list = []
        if barcodes:
            barcode_list = [b.strip() for b in barcodes.split(",") if b.strip()]
        
        if not fhrsid_list and not barcode_list:
            raise HTTPException(
                status_code=400,
                detail="Must provide at least one establishment ID or product barcode"
            )
        
        service = IntelligenceService(db)
        result = service.compare_establishments_and_products(
            fhrsids=fhrsid_list,
            barcodes=barcode_list
        )
        
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {str(e)}")
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/category/{category}/insights")
async def get_category_insights(
    category: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive insights for a product category.
    
    Returns statistics, top products, and eco-friendly recommendations.
    """
    start_time = time.time()
    
    try:
        service = IntelligenceService(db)
        result = service.get_category_insights(category)
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": result,
            "meta": {
                "response_time_ms": round(process_time, 2)
            }
        }
    except Exception as e:
        logger.error(f"Category insights error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")