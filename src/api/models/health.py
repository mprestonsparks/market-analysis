"""Health check models."""
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

class DependencyStatus(BaseModel):
    """Status of a dependency service."""
    connected: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    last_successful_connection: Optional[datetime] = None

class SystemMetrics(BaseModel):
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    uptime_seconds: int
    request_count: int
    average_response_time_ms: float

class HealthResponse(BaseModel):
    """Enhanced health check response."""
    status: str
    version: str
    environment: str
    timestamp: datetime
    git_commit: Optional[str] = None
    dependencies: Dict[str, DependencyStatus]
    metrics: SystemMetrics
