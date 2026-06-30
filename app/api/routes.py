from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional
from datetime import datetime
from app.api.schemas import (
    Location,
    Measurement,
    LocationStats,
    DailyAggregate,
    ExportRequest,
    PipelineResponse,
    HealthResponse
)
from app.services.location_service import LocationService
from app.services.export_service import ExportService
from app.core.database import db_manager
from app.config.settings import settings
from app.config.logging_config import logger
from app.websocket.manager import manager

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        with db_manager.get_connection() as conn:
            conn.execute("SELECT 1")
        
        return HealthResponse(
            status="healthy",
            version=settings.APP_VERSION,
            database="connected",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/locations", response_model=List[Location])
async def get_locations(
    active_only: bool = True,
    country: Optional[str] = None,
    city: Optional[str] = None
):
    """Get all locations."""
    service = LocationService()
    locations = service.get_all_locations(
        active_only=active_only,
        country=country,
        city=city
    )
    return locations


@router.get("/locations/{location_id}", response_model=Location)
async def get_location(location_id: int):
    """Get a specific location."""
    service = LocationService()
    location = service.get_location_by_id(location_id)
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return location


@router.get("/locations/{location_id}/stats", response_model=LocationStats)
async def get_location_statistics(location_id: int):
    """Get statistics for a location."""
    service = LocationService()
    stats = service.get_location_statistics(location_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return stats


@router.get("/locations/search")
async def search_locations(q: str = Query(..., min_length=1)):
    """Search locations."""
    service = LocationService()
    locations = service.search_locations(q)
    return locations


@router.get("/measurements/latest")
async def get_latest_measurements(
    location_id: Optional[int] = None,
    parameter: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get latest measurements."""
    query = """
    SELECT 
        location_id,
        location,
        latitude,
        longitude,
        parameter,
        unit,
        value,
        measurement_time,
        quality_score
    FROM presentation.latest_measurements
    WHERE quality_score > 0.5
    """
    
    params = {}
    
    if location_id:
        query += " AND location_id = $location_id"
        params["location_id"] = location_id
    
    if parameter:
        query += " AND parameter = $parameter"
        params["parameter"] = parameter
    
    query += " ORDER BY measurement_time DESC LIMIT $limit"
    params["limit"] = limit
    
    try:
        with db_manager.get_connection() as conn:
            result = conn.execute(query, params)
            return result.df().to_dict("records")
    except Exception as e:
        logger.error(f"Error fetching latest measurements: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching measurements")


@router.get("/measurements/daily")
async def get_daily_aggregates(
    location_id: Optional[int] = None,
    parameter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000)
):
    """Get daily aggregated measurements."""
    query = """
    SELECT 
        location_id,
        location,
        parameter,
        unit,
        measurement_date,
        avg_value,
        min_value,
        max_value,
        std_value,
        measurement_count,
        avg_quality
    FROM presentation.daily_aggregates
    WHERE 1=1
    """
    
    params = {}
    
    if location_id:
        query += " AND location_id = $location_id"
        params["location_id"] = location_id
    
    if parameter:
        query += " AND parameter = $parameter"
        params["parameter"] = parameter
    
    if date_from:
        query += " AND measurement_date >= $date_from"
        params["date_from"] = date_from
    
    if date_to:
        query += " AND measurement_date <= $date_to"
        params["date_to"] = date_to
    
    query += " ORDER BY measurement_date DESC LIMIT $limit"
    params["limit"] = limit
    
    try:
        with db_manager.get_connection() as conn:
            result = conn.execute(query, params)
            return result.df().to_dict("records")
    except Exception as e:
        logger.error(f"Error fetching daily aggregates: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching aggregates")


@router.post("/export")
async def export_data(request: ExportRequest):
    """Export data in specified format."""
    try:
        export_service = ExportService()
        data = export_service.get_export_data(
            format=request.format,
            location_id=request.location_id,
            parameter=request.parameter,
            date_from=request.date_from,
            date_to=request.date_to
        )
        
        from fastapi.responses import Response
        media_types = {
            "csv": "text/csv",
            "json": "application/json",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "parquet": "application/octet-stream"
        }
        
        return Response(
            content=data,
            media_type=media_types.get(request.format, "application/octet-stream"),
            headers={
                "Content-Disposition": f"attachment; filename=air_quality_export.{request.format}"
            }
        )
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/pipeline/sync", response_model=PipelineResponse)
async def sync_pipeline():
    """Trigger pipeline sync."""
    try:
        from app.pipeline.orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator()
        
        results = orchestrator.run_pipeline(
            sync_locations=True,
            collect_latest=True
        )
        
        return PipelineResponse(
            status="success",
            message="Pipeline sync completed",
            data=results
        )
    except Exception as e:
        logger.error(f"Pipeline sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline sync failed: {str(e)}")


@router.post("/pipeline/locations/sync", response_model=PipelineResponse)
async def sync_locations(
    country: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000)
):
    """Sync locations from OpenAQ."""
    try:
        service = LocationService()
        results = service.sync_locations_from_api(
            country=country,
            city=city,
            limit=limit
        )
        
        return PipelineResponse(
            status="success",
            message="Location sync completed",
            data=results
        )
    except Exception as e:
        logger.error(f"Location sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Location sync failed: {str(e)}")


@router.get("/stats/summary")
async def get_summary_stats():
    """Get overall system statistics."""
    try:
        queries = {
            "total_locations": "SELECT COUNT(*) FROM staging.locations WHERE is_active = TRUE",
            "total_measurements": "SELECT COUNT(*) FROM raw.measurements",
            "total_parameters": "SELECT COUNT(DISTINCT parameter) FROM raw.measurements",
            "latest_measurement": "SELECT MAX(measurement_time) FROM raw.measurements"
        }
        
        stats = {}
        with db_manager.get_connection() as conn:
            for key, query in queries.items():
                result = conn.execute(query)
                stats[key] = result.fetchone()[0]
        
        return stats
    except Exception as e:
        logger.error(f"Error fetching summary stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching statistics")


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            logger.info(f"Received message from client {client_id}: {data}")
            
            # Echo back or process message
            await manager.send_personal_message(
                {"type": "echo", "message": f"Received: {data}"},
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        manager.disconnect(websocket, client_id)
