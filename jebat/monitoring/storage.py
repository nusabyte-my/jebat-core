"""
Storage layer for JEBAT monitoring subsystem.
Handles persistence of metrics to TimescaleDB.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import asyncpg

from .models import MonitoringSnapshot

logger = logging.getLogger(__name__)

class MonitoringStorage:
    """
    Stores monitoring metrics in TimescaleDB.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize the monitoring storage.
        
        Args:
            db_config: Database connection configuration
        """
        self.db_config = db_config
        self.pool: Optional[asyncpg.Pool] = None
        self._is_connected = False
        
        logger.info("MonitoringStorage initialized")
    
    async def connect(self):
        """Connect to the database."""
        if self._is_connected:
            logger.warning("MonitoringStorage is already connected")
            return
        
        try:
            self.pool = await asyncpg.create_pool(**self.db_config)
            await self._ensure_schema()
            self._is_connected = True
            logger.info("MonitoringStorage connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the database."""
        if not self._is_connected:
            logger.warning("MonitoringStorage is not connected")
            return
        
        if self.pool:
            await self.pool.close()
            self.pool = None
        self._is_connected = False
        logger.info("MonitoringStorage disconnected from database")
    
    async def _ensure_schema(self):
        """Ensure the database schema exists."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            # Enable TimescaleDB extension if not already enabled
            try:
                await conn.execute('CREATE EXTENSION IF NOT EXISTS timescaledb;')
                logger.info("TimescaleDB extension enabled")
            except Exception as e:
                logger.warning(f"Could not enable TimescaleDB extension (may already be enabled): {e}")
            
            # Create system_metrics table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    time TIMESTAMPTZ NOT NULL,
                    component TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value DOUBLE PRECISION,
                    metric_labels JSONB,
                    id UUID DEFAULT gen_random_uuid()
                );
            ''')
            
            # Create hypertable for time-series data
            try:
                await conn.execute('''
                    SELECT create_hypertable('system_metrics', 'time', 
                                          if_not_exists => TRUE);
                ''')
                logger.info("System metrics hypertable created/verified")
            except Exception as e:
                logger.error(f"Failed to create hypertable: {e}")
                raise
            
            # Create indexes for better query performance
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_system_metrics_time 
                ON system_metrics (time DESC);
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_system_metrics_component 
                ON system_metrics (component);
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_system_metrics_metric_name 
                ON system_metrics (metric_name);
            ''')
            
            # Create materialized view for 1-hour aggregates
            try:
                await conn.execute('''
                    DROP MATERIALIZED VIEW IF EXISTS system_metrics_1h;
                ''')
                await conn.execute('''
                    CREATE MATERIALIZED VIEW system_metrics_1h
                    WITH (timescaledb.continuous) AS
                    SELECT 
                        time_bucket('1 hour', time) AS bucket,
                        component,
                        metric_name,
                        AVG(metric_value) AS avg_value,
                        MAX(metric_value) AS max_value,
                        MIN(metric_value) AS min_value,
                        COUNT(*) AS sample_count
                    FROM system_metrics
                    GROUP BY bucket, component, metric_name
                    WITH NO DATA;
                ''')
                
                # Refresh the policy
                await conn.execute('''
                    SELECT refresh_continuous_aggregate('system_metrics_1h');
                ''')
                logger.info("Continuous aggregate for 1-hour metrics created")
            except Exception as e:
                logger.error(f"Failed to create continuous aggregate: {e}")
                # Don't fail completely if this fails
            
            logger.info("Monitoring storage schema ensured")
    
    async def store_snapshot(self, snapshot: MonitoringSnapshot):
        """
        Store a monitoring snapshot.
        
        Args:
            snapshot: Monitoring snapshot to store
        """
        if not self._is_connected or not self.pool:
            raise RuntimeError("Storage not connected to database")
        
        # Convert snapshot to individual metric records
        records = []
        for component_name, component_stats in snapshot.components.items():
            for metric_name, metric_value in component_stats.metrics.items():
                records.append((
                    component_stats.timestamp,
                    component_name,
                    metric_name,
                    metric_value,
                    component_stats.labels  # Store as JSONB
                ))
        
        if not records:
            logger.warning("No metrics to store in snapshot")
            return
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany('''
                        INSERT INTO system_metrics 
                        (time, component, metric_name, metric_value, metric_labels)
                        VALUES ($1, $2, $3, $4, $5)
                    ''', records)
            
            logger.debug(f"Stored {len(records)} metric records")
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
            raise
    
    async def get_latest_metrics(self, component: Optional[str] = None, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the latest metrics from storage.
        
        Args:
            component: Optional component filter
            limit: Maximum number of records to return
            
        Returns:
            List of metric records
        """
        if not self._is_connected or not self.pool:
            raise RuntimeError("Storage not connected to database")
        
        async with self.pool.acquire() as conn:
            if component:
                rows = await conn.fetch('''
                    SELECT time, component, metric_name, metric_value, metric_labels
                    FROM system_metrics
                    WHERE component = $1
                    ORDER BY time DESC
                    LIMIT $2
                ''', component, limit)
            else:
                rows = await conn.fetch('''
                    SELECT time, component, metric_name, metric_value, metric_labels
                    FROM system_metrics
                    ORDER BY time DESC
                    LIMIT $1
                ''', limit)
            
            return [dict(row) for row in rows]
    
    async def get_metrics_time_range(self, component: str, metric_name: str,
                                   start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Get metrics for a specific component and metric within a time range.
        
        Args:
            component: Component name
            metric_name: Metric name
            start_time: Start time
            end_time: End time
            
        Returns:
            List of metric records
        """
        if not self._is_connected or not self.pool:
            raise RuntimeError("Storage not connected to database")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT time, component, metric_name, metric_value, metric_labels
                FROM system_metrics
                WHERE component = $1 AND metric_name = $2 
                AND time >= $3 AND time <= $4
                ORDER BY time
            ''', component, metric_name, start_time, end_time)
            
            return [dict(row) for row in rows]
    
    async def get_aggregated_metrics(self, component: str, metric_name: str,
                                   start_time: datetime, end_time: datetime,
                                   interval: str = '1 hour') -> List[Dict[str, Any]]:
        """
        Get aggregated metrics for a time range.
        
        Args:
            component: Component name
            metric_name: Metric name
            start_time: Start time
            end_time: End time
            interval: Time bucket interval (e.g., '1 hour', '15 minutes')
            
        Returns:
            List of aggregated metric records
        """
        if not self._is_connected or not self.pool:
            raise RuntimeError("Storage not connected to database")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT 
                    time_bucket($1, time) AS bucket,
                    AVG(metric_value) AS avg_value,
                    MAX(metric_value) AS max_value,
                    MIN(metric_value) AS min_value,
                    COUNT(*) AS sample_count
                FROM system_metrics
                WHERE component = $2 AND metric_name = $3 
                AND time >= $4 AND time <= $5
                GROUP BY bucket
                ORDER BY bucket
            ''', interval, component, metric_name, start_time, end_time)
            
            return [dict(row) for row in rows]

# Global storage instance
_storage: Optional[MonitoringStorage] = None

def get_storage() -> Optional[MonitoringStorage]:
    """Get the global monitoring storage instance."""
    return _storage

def initialize_storage(db_config: Dict[str, Any]) -> MonitoringStorage:
    """Initialize the global monitoring storage."""
    global _storage
    _storage = MonitoringStorage(db_config)
    return _storage