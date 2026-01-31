"""
API routes for FSA establishment endpoints.
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.repositories.fsa_repository import FSARepository

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/nearby")
async def get_nearby_establishments(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    radius: int = Query(1, description="Search radius in miles", ge=1, le=10),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Find establishments near geographic coordinates.
    
    Returns establishments within the specified radius sorted by distance.
    """
    start_time = time.time()
    
    try:
        repo = FSARepository(db)
        results = repo.get_nearby_establishments(
            latitude=lat,
            longitude=lon,
            radius_miles=radius,
            limit=limit
        )
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": results,
            "meta": {
                "count": len(results),
                "search_radius_miles": radius,
                "coordinates": {"lat": lat, "lon": lon},
                "response_time_ms": round(process_time, 2)
            }
        }
    except Exception as e:
        logger.error(f"Nearby search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.get("/search")
async def search_establishments(
    name: Optional[str] = Query(None, description="Business name to search"),
    postcode: Optional[str] = Query(None, description="UK postcode"),
    rating_value: Optional[str] = Query(None, description="Rating filter (0-5)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Search for food establishments by name, postcode, or rating.
    
    Returns establishment hygiene rating data from the FSA.
    """
    start_time = time.time()
    
    try:
        repo = FSARepository(db)
        results = repo.search_establishments(
            name=name,
            postcode=postcode,
            rating_value=rating_value,
            limit=limit
        )
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": results,
            "meta": {
                "count": len(results),
                "limit": limit,
                "response_time_ms": round(process_time, 2)
            }
        }
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/statistics/{postcode}")
async def get_postcode_statistics(
    postcode: str,
    db: Session = Depends(get_db)
):
    """
    Get hygiene rating statistics for a postcode area.
    
    Returns aggregated statistics including rating distribution and averages.
    """
    start_time = time.time()
    
    try:
        repo = FSARepository(db)
        stats = repo.get_statistics_by_postcode(postcode)
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": stats,
            "meta": {
                "response_time_ms": round(process_time, 2)
            }
        }
    except Exception as e:
        logger.error(f"Statistics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
@router.get("/{fhrsid}")
async def get_establishment(
    fhrsid: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific establishment by FHRSID.
    
    Returns comprehensive hygiene rating data including scores and location.
    """
    start_time = time.time()
    
    try:
        repo = FSARepository(db)
        result = repo.get_establishment(fhrsid)
        
        if not result:
            raise HTTPException(status_code=404, detail="Establishment not found")
        
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
        logger.error(f"Get establishment error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
