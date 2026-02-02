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
# ADD THIS IMPORT:
from src.api.services.fsa_service import get_fsa_service, FSAAPIError

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


# ADD THIS NEW ENDPOINT that uses FSA Service to fetch fresh data from API:
@router.get("/search/live")
async def search_establishments_live(
    postcode: Optional[str] = Query(None, description="UK postcode"),
    name: Optional[str] = Query(None, description="Business name to search"),
    local_authority: Optional[str] = Query(None, description="Local authority name"),
    rating_key: Optional[str] = Query(None, description="Rating filter (0-5)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    page_number: int = Query(1, ge=1, description="Page number")
):
    """
    Search for establishments using live FSA API data (not from database).
    
    This endpoint fetches fresh data directly from the FSA API.
    Use this when you need the most up-to-date information.
    """
    start_time = time.time()
    
    try:
        fsa_service = get_fsa_service()
        
        # Choose search method based on parameters
        if postcode and not local_authority:
            # Search by postcode (with automatic local authority lookup)
            results = fsa_service.search_establishments_by_postcode(
                postcode=postcode,
                name=name,
                rating_key=rating_key,
                page_number=page_number,
                page_size=page_size
            )
        elif local_authority:
            # Search by local authority name
            results = fsa_service.search_establishments_by_area(
                local_authority_name=local_authority,
                name=name,
                postcode=postcode,
                rating_key=rating_key,
                page_number=page_number,
                page_size=page_size
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'postcode' or 'local_authority' parameter is required"
            )
        
        establishments = results.get('establishments', [])
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": establishments,
            "meta": {
                "count": len(establishments),
                "page_number": page_number,
                "page_size": page_size,
                "total_count": results.get('meta', {}).get('totalCount'),
                "total_pages": results.get('meta', {}).get('totalPages'),
                "response_time_ms": round(process_time, 2),
                "data_source": "FSA API (live)"
            }
        }
    except FSAAPIError as e:
        logger.error(f"FSA API error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"FSA API error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Live search error: {str(e)}", exc_info=True)
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


# ADD OPTIONAL: Endpoint to get live establishment details from API
@router.get("/{fhrsid}/live")
async def get_establishment_live(
    fhrsid: int
):
    """
    Get establishment details directly from FSA API (live data).
    
    Use this when you need the most current information for an establishment.
    """
    start_time = time.time()
    
    try:
        fsa_service = get_fsa_service()
        result = fsa_service.get_establishment_details(fhrsid)
        
        process_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": result,
            "meta": {
                "response_time_ms": round(process_time, 2),
                "data_source": "FSA API (live)"
            }
        }
    except FSAAPIError as e:
        logger.error(f"FSA API error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"FSA API error: {str(e)}")
    except Exception as e:
        logger.error(f"Get establishment error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
