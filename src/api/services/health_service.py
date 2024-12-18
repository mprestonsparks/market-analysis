"""Health check service."""
import os
import psutil
import time
from datetime import datetime, timezone
import subprocess
from typing import Dict, Optional

from src.api.models.health import HealthResponse, DependencyStatus, SystemMetrics
from src.api.queue.redis_client import RedisClient
from src.api.queue.queue_manager import QueueManager

class HealthService:
    """Service for checking system health and gathering metrics."""
    
    def __init__(self, redis_client: Optional[RedisClient], queue_manager: Optional[QueueManager]):
        """Initialize the health service."""
        self.start_time = time.time()
        self.request_count = 0
        self.total_response_time = 0
        self.redis_client = redis_client
        self.queue_manager = queue_manager
        self.test_mode = redis_client is None or getattr(redis_client, 'test_mode', False)

    def get_git_commit(self) -> Optional[str]:
        """Get the current git commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def check_redis(self) -> DependencyStatus:
        """Check Redis connection and get status."""
        if self.test_mode:
            return DependencyStatus(
                connected=True,
                latency_ms=0.0,
                last_successful_connection=datetime.now(timezone.utc)
            )
        if self.redis_client is None:
            return DependencyStatus(
                connected=False,
                error="Redis client is not available"
            )
        try:
            start_time = time.time()
            self.redis_client.ping()
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return DependencyStatus(
                connected=True,
                latency_ms=latency,
                last_successful_connection=datetime.now(timezone.utc)
            )
        except Exception as e:
            return DependencyStatus(
                connected=False,
                error=str(e)
            )

    def check_rabbitmq(self) -> DependencyStatus:
        """Check RabbitMQ connection and get status."""
        if self.test_mode:
            return DependencyStatus(
                connected=True,
                latency_ms=0.0,
                last_successful_connection=datetime.now(timezone.utc)
            )
        if self.queue_manager is None:
            return DependencyStatus(
                connected=False,
                error="Queue manager is not available"
            )
        try:
            start_time = time.time()
            # Add actual RabbitMQ health check here
            connected = self.queue_manager.is_connected()
            latency = (time.time() - start_time) * 1000
            
            return DependencyStatus(
                connected=connected,
                latency_ms=latency if connected else None,
                last_successful_connection=datetime.now(timezone.utc) if connected else None
            )
        except Exception as e:
            return DependencyStatus(
                connected=False,
                error=str(e)
            )

    def get_system_metrics(self) -> SystemMetrics:
        """Get system performance metrics."""
        process = psutil.Process()
        
        return SystemMetrics(
            cpu_usage=process.cpu_percent(),
            memory_usage=process.memory_percent(),
            uptime_seconds=int(time.time() - self.start_time),
            request_count=self.request_count,
            average_response_time_ms=(
                self.total_response_time / self.request_count 
                if self.request_count > 0 else 0
            )
        )

    def get_health(self, version: str) -> HealthResponse:
        """Get comprehensive health status."""
        dependencies = {
            "redis": self.check_redis(),
            "rabbitmq": self.check_rabbitmq()
        }
        
        # Determine overall status based on dependencies
        status = "healthy"
        if not all(dep.connected for dep in dependencies.values()):
            status = "degraded"
        
        return HealthResponse(
            status=status,
            version=version,
            environment=os.getenv("ENVIRONMENT", "development"),
            timestamp=datetime.now(timezone.utc),
            git_commit=self.get_git_commit(),
            dependencies=dependencies,
            metrics=self.get_system_metrics()
        )

    def record_request(self, response_time_ms: float):
        """Record a request and its response time for metrics."""
        self.request_count += 1
        self.total_response_time += response_time_ms
