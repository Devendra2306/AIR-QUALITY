from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Location(BaseModel):
    location_id: int
    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    is_active: bool = True


class Measurement(BaseModel):
    location_id: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    parameter: str
    unit: Optional[str] = None
    value: float
    measurement_time: datetime
    quality_score: Optional[float] = None


class LocationStats(BaseModel):
    location_id: int
    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    parameter_count: int
    total_measurements: int
    last_measurement_time: Optional[datetime] = None
    avg_quality_score: Optional[float] = None


class DailyAggregate(BaseModel):
    location_id: int
    location: Optional[str] = None
    parameter: str
    unit: Optional[str] = None
    measurement_date: datetime
    avg_value: float
    min_value: float
    max_value: float
    std_value: Optional[float] = None
    measurement_count: int
    avg_quality: Optional[float] = None


class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(csv|json|excel|parquet)$")
    location_id: Optional[int] = None
    parameter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class PipelineResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: datetime
