# Fleet-wide Analytics

**Last Updated:** 2025-12-09  
**Status:** Design Phase  
**Version:** 1.0

## Overview

Fleet-wide Analytics provides aggregated insights across multiple MODAX installations, enabling organizations to analyze trends, identify patterns, and optimize operations across multiple facilities and locations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Fleet Analytics Platform                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Data Aggregation Layer                   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │    │
│  │  │ Location │  │ Location │  │ Location │         │    │
│  │  │    A     │  │    B     │  │    C     │         │    │
│  │  │ (50 dev) │  │ (30 dev) │  │ (40 dev) │         │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘         │    │
│  └───────┼─────────────┼─────────────┼──────────────────┘  │
│          │             │             │                      │
│  ┌───────▼─────────────▼─────────────▼──────────────────┐  │
│  │         Fleet Data Warehouse (TimescaleDB)           │  │
│  │  - Aggregated sensor data                            │  │
│  │  - Device metadata                                   │  │
│  │  - Performance metrics                               │  │
│  │  - Failure events                                    │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │         Analytics Engine                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐      │  │
│  │  │ Cross-   │  │ Benchmark│  │  Predictive  │      │  │
│  │  │ Location │  │ Analysis │  │  Modeling    │      │  │
│  │  │ Trends   │  │          │  │              │      │  │
│  │  └──────────┘  └──────────┘  └──────────────┘      │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │         Visualization & Reporting                    │  │
│  │  - Executive dashboards                              │  │
│  │  - Location comparison                               │  │
│  │  - Fleet health overview                             │  │
│  │  - Cost analysis                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### Fleet Hierarchy
```python
# python-control-layer/models/fleet.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Organization:
    """Top-level organization"""
    id: str
    name: str
    created_at: datetime
    settings: dict

@dataclass
class Location:
    """Physical location/facility"""
    id: str
    organization_id: str
    name: str
    address: str
    timezone: str
    coordinates: tuple  # (latitude, longitude)
    device_count: int
    created_at: datetime

@dataclass
class DeviceFleet:
    """Collection of devices across locations"""
    organization_id: str
    total_devices: int
    active_devices: int
    locations: List[Location]
    device_types: dict  # {type: count}

@dataclass
class FleetMetrics:
    """Aggregated fleet metrics"""
    timestamp: datetime
    organization_id: str
    location_id: Optional[str]
    
    # Performance metrics
    avg_uptime: float
    avg_efficiency: float
    avg_energy_consumption: float
    
    # Maintenance metrics
    total_failures: int
    mtbf: float  # Mean Time Between Failures
    mttr: float  # Mean Time To Repair
    
    # Operational metrics
    total_production_hours: float
    total_downtime_hours: float
    oee: float  # Overall Equipment Effectiveness
```

### Database Schema
```sql
-- Organizations table
CREATE TABLE organizations (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

-- Locations table
CREATE TABLE locations (
    id VARCHAR(64) PRIMARY KEY,
    organization_id VARCHAR(64) REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    timezone VARCHAR(64),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fleet metrics (TimescaleDB hypertable)
CREATE TABLE fleet_metrics (
    timestamp TIMESTAMPTZ NOT NULL,
    organization_id VARCHAR(64) NOT NULL,
    location_id VARCHAR(64),
    
    -- Performance
    avg_uptime DOUBLE PRECISION,
    avg_efficiency DOUBLE PRECISION,
    avg_energy_consumption DOUBLE PRECISION,
    
    -- Maintenance
    total_failures INTEGER,
    mtbf DOUBLE PRECISION,
    mttr DOUBLE PRECISION,
    
    -- Operational
    total_production_hours DOUBLE PRECISION,
    total_downtime_hours DOUBLE PRECISION,
    oee DOUBLE PRECISION,
    
    PRIMARY KEY (organization_id, location_id, timestamp)
);

-- Convert to hypertable
SELECT create_hypertable('fleet_metrics', 'timestamp');

-- Create continuous aggregates for fleet analytics
CREATE MATERIALIZED VIEW fleet_metrics_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    organization_id,
    location_id,
    AVG(avg_uptime) as avg_uptime,
    AVG(avg_efficiency) as avg_efficiency,
    AVG(avg_energy_consumption) as avg_energy_consumption,
    SUM(total_failures) as total_failures,
    AVG(mtbf) as mtbf,
    AVG(mttr) as mttr,
    AVG(oee) as oee
FROM fleet_metrics
GROUP BY hour, organization_id, location_id;

CREATE MATERIALIZED VIEW fleet_metrics_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS day,
    organization_id,
    location_id,
    AVG(avg_uptime) as avg_uptime,
    AVG(avg_efficiency) as avg_efficiency,
    AVG(avg_energy_consumption) as avg_energy_consumption,
    SUM(total_failures) as total_failures,
    AVG(mtbf) as mtbf,
    AVG(mttr) as mttr,
    AVG(oee) as oee
FROM fleet_metrics
GROUP BY day, organization_id, location_id;
```

## Analytics Services

### 1. Cross-Location Comparison
```python
# python-control-layer/analytics/fleet_analyzer.py
from typing import List, Dict
import pandas as pd

class FleetAnalyzer:
    """Analyze metrics across multiple locations"""
    
    async def compare_locations(
        self,
        organization_id: str,
        location_ids: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Compare performance metrics across locations
        
        Returns DataFrame with location comparisons
        """
        query = """
            SELECT 
                location_id,
                l.name as location_name,
                AVG(fm.avg_uptime) as avg_uptime,
                AVG(fm.avg_efficiency) as avg_efficiency,
                AVG(fm.oee) as oee,
                SUM(fm.total_failures) as total_failures,
                AVG(fm.mtbf) as mtbf,
                AVG(fm.mttr) as mttr
            FROM fleet_metrics fm
            JOIN locations l ON fm.location_id = l.id
            WHERE fm.organization_id = $1
                AND fm.location_id = ANY($2)
                AND fm.timestamp BETWEEN $3 AND $4
            GROUP BY location_id, l.name
            ORDER BY oee DESC
        """
        
        data = await self.db.fetch(
            query,
            organization_id,
            location_ids,
            start_date,
            end_date
        )
        
        return pd.DataFrame(data)
    
    async def identify_best_performers(
        self,
        organization_id: str,
        metric: str = 'oee',
        top_n: int = 5
    ) -> List[Dict]:
        """
        Identify top-performing locations
        
        Args:
            organization_id: Organization ID
            metric: Metric to rank by (oee, uptime, efficiency)
            top_n: Number of top locations to return
        """
        query = f"""
            SELECT 
                location_id,
                l.name as location_name,
                AVG(fm.{metric}) as metric_value
            FROM fleet_metrics fm
            JOIN locations l ON fm.location_id = l.id
            WHERE fm.organization_id = $1
                AND fm.timestamp > NOW() - INTERVAL '30 days'
            GROUP BY location_id, l.name
            ORDER BY metric_value DESC
            LIMIT $2
        """
        
        return await self.db.fetch(query, organization_id, top_n)
    
    async def identify_underperformers(
        self,
        organization_id: str,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Identify locations below performance threshold
        
        Returns locations with OEE below threshold
        """
        query = """
            SELECT 
                location_id,
                l.name as location_name,
                AVG(fm.oee) as avg_oee,
                AVG(fm.avg_uptime) as avg_uptime,
                SUM(fm.total_failures) as total_failures
            FROM fleet_metrics fm
            JOIN locations l ON fm.location_id = l.id
            WHERE fm.organization_id = $1
                AND fm.timestamp > NOW() - INTERVAL '30 days'
            GROUP BY location_id, l.name
            HAVING AVG(fm.oee) < $2
            ORDER BY avg_oee ASC
        """
        
        return await self.db.fetch(query, organization_id, threshold)
```

### 2. Trend Analysis
```python
# python-control-layer/analytics/trend_analyzer.py
class TrendAnalyzer:
    """Analyze trends across the fleet"""
    
    async def analyze_failure_trends(
        self,
        organization_id: str,
        period: str = 'monthly'
    ) -> pd.DataFrame:
        """
        Analyze failure trends over time
        
        Returns trend data for failures across fleet
        """
        interval = '1 month' if period == 'monthly' else '1 week'
        
        query = f"""
            SELECT 
                time_bucket('{interval}', timestamp) as period,
                location_id,
                l.name as location_name,
                SUM(total_failures) as failures,
                AVG(mtbf) as avg_mtbf
            FROM fleet_metrics fm
            JOIN locations l ON fm.location_id = l.id
            WHERE fm.organization_id = $1
                AND fm.timestamp > NOW() - INTERVAL '1 year'
            GROUP BY period, location_id, l.name
            ORDER BY period, location_id
        """
        
        data = await self.db.fetch(query, organization_id)
        df = pd.DataFrame(data)
        
        # Calculate trend
        df['trend'] = df.groupby('location_id')['failures'].pct_change()
        
        return df
    
    async def forecast_maintenance_demand(
        self,
        organization_id: str,
        forecast_days: int = 30
    ) -> Dict:
        """
        Forecast maintenance demand for the fleet
        
        Uses historical failure rates to predict maintenance needs
        """
        # Get historical failure rates
        query = """
            SELECT 
                date_trunc('day', timestamp) as day,
                SUM(total_failures) as daily_failures
            FROM fleet_metrics
            WHERE organization_id = $1
                AND timestamp > NOW() - INTERVAL '90 days'
            GROUP BY day
            ORDER BY day
        """
        
        historical_data = await self.db.fetch(query, organization_id)
        df = pd.DataFrame(historical_data)
        
        # Simple moving average forecast
        avg_daily_failures = df['daily_failures'].mean()
        std_daily_failures = df['daily_failures'].std()
        
        # Forecast with confidence intervals
        forecast = {
            'forecast_period_days': forecast_days,
            'expected_failures': avg_daily_failures * forecast_days,
            'confidence_interval_95': {
                'lower': (avg_daily_failures - 1.96 * std_daily_failures) * forecast_days,
                'upper': (avg_daily_failures + 1.96 * std_daily_failures) * forecast_days
            },
            'recommended_spare_parts': self._calculate_spare_parts_needs(
                avg_daily_failures * forecast_days
            )
        }
        
        return forecast
```

### 3. Benchmarking
```python
# python-control-layer/analytics/benchmarking.py
class FleetBenchmarking:
    """Benchmark performance against fleet averages and industry standards"""
    
    async def benchmark_location(
        self,
        organization_id: str,
        location_id: str
    ) -> Dict:
        """
        Benchmark a location against fleet averages
        
        Returns comparison of location vs fleet averages
        """
        query = """
            WITH location_metrics AS (
                SELECT 
                    AVG(avg_uptime) as uptime,
                    AVG(oee) as oee,
                    AVG(mtbf) as mtbf,
                    AVG(mttr) as mttr,
                    AVG(avg_energy_consumption) as energy
                FROM fleet_metrics
                WHERE organization_id = $1
                    AND location_id = $2
                    AND timestamp > NOW() - INTERVAL '30 days'
            ),
            fleet_averages AS (
                SELECT 
                    AVG(avg_uptime) as uptime,
                    AVG(oee) as oee,
                    AVG(mtbf) as mtbf,
                    AVG(mttr) as mttr,
                    AVG(avg_energy_consumption) as energy
                FROM fleet_metrics
                WHERE organization_id = $1
                    AND timestamp > NOW() - INTERVAL '30 days'
            )
            SELECT 
                lm.uptime as location_uptime,
                fa.uptime as fleet_avg_uptime,
                (lm.uptime - fa.uptime) / fa.uptime * 100 as uptime_diff_pct,
                
                lm.oee as location_oee,
                fa.oee as fleet_avg_oee,
                (lm.oee - fa.oee) / fa.oee * 100 as oee_diff_pct,
                
                lm.mtbf as location_mtbf,
                fa.mtbf as fleet_avg_mtbf,
                (lm.mtbf - fa.mtbf) / fa.mtbf * 100 as mtbf_diff_pct,
                
                lm.mttr as location_mttr,
                fa.mttr as fleet_avg_mttr,
                (lm.mttr - fa.mttr) / fa.mttr * 100 as mttr_diff_pct,
                
                lm.energy as location_energy,
                fa.energy as fleet_avg_energy,
                (lm.energy - fa.energy) / fa.energy * 100 as energy_diff_pct
            FROM location_metrics lm, fleet_averages fa
        """
        
        result = await self.db.fetchrow(query, organization_id, location_id)
        
        return {
            'uptime': {
                'location': result['location_uptime'],
                'fleet_average': result['fleet_avg_uptime'],
                'difference_pct': result['uptime_diff_pct'],
                'status': 'above_average' if result['uptime_diff_pct'] > 0 else 'below_average'
            },
            'oee': {
                'location': result['location_oee'],
                'fleet_average': result['fleet_avg_oee'],
                'difference_pct': result['oee_diff_pct'],
                'status': 'above_average' if result['oee_diff_pct'] > 0 else 'below_average'
            },
            'mtbf': {
                'location': result['location_mtbf'],
                'fleet_average': result['fleet_avg_mtbf'],
                'difference_pct': result['mtbf_diff_pct'],
                'status': 'above_average' if result['mtbf_diff_pct'] > 0 else 'below_average'
            },
            'mttr': {
                'location': result['location_mttr'],
                'fleet_average': result['fleet_avg_mttr'],
                'difference_pct': result['mttr_diff_pct'],
                'status': 'below_average' if result['mttr_diff_pct'] > 0 else 'above_average'  # Lower is better
            },
            'energy_consumption': {
                'location': result['location_energy'],
                'fleet_average': result['fleet_avg_energy'],
                'difference_pct': result['energy_diff_pct'],
                'status': 'below_average' if result['energy_diff_pct'] > 0 else 'above_average'  # Lower is better
            }
        }
```

## API Endpoints

```python
# python-control-layer/fleet_api.py
from fastapi import APIRouter, Depends
from auth import UserContext, get_user_context, require_admin

router = APIRouter(prefix="/fleet", tags=["fleet"])

@router.get("/organizations/{org_id}/overview")
async def get_fleet_overview(
    org_id: str,
    user: UserContext = Depends(get_user_context)
):
    """Get fleet-wide overview for an organization"""
    analyzer = FleetAnalyzer()
    
    return {
        'total_devices': await analyzer.get_total_devices(org_id),
        'total_locations': await analyzer.get_total_locations(org_id),
        'overall_oee': await analyzer.get_overall_oee(org_id),
        'overall_uptime': await analyzer.get_overall_uptime(org_id),
        'total_failures_last_30d': await analyzer.get_total_failures(org_id, days=30)
    }

@router.get("/organizations/{org_id}/locations/compare")
async def compare_locations(
    org_id: str,
    location_ids: List[str],
    start_date: datetime,
    end_date: datetime,
    user: UserContext = Depends(get_user_context)
):
    """Compare performance across multiple locations"""
    analyzer = FleetAnalyzer()
    comparison = await analyzer.compare_locations(
        org_id,
        location_ids,
        start_date,
        end_date
    )
    
    return comparison.to_dict(orient='records')

@router.get("/organizations/{org_id}/locations/{location_id}/benchmark")
async def benchmark_location(
    org_id: str,
    location_id: str,
    user: UserContext = Depends(get_user_context)
):
    """Benchmark a location against fleet averages"""
    benchmarking = FleetBenchmarking()
    return await benchmarking.benchmark_location(org_id, location_id)

@router.get("/organizations/{org_id}/trends/failures")
async def get_failure_trends(
    org_id: str,
    period: str = 'monthly',
    user: UserContext = Depends(get_user_context)
):
    """Get failure trends across the fleet"""
    analyzer = TrendAnalyzer()
    trends = await analyzer.analyze_failure_trends(org_id, period)
    return trends.to_dict(orient='records')

@router.get("/organizations/{org_id}/forecast/maintenance")
async def forecast_maintenance(
    org_id: str,
    forecast_days: int = 30,
    user: UserContext = Depends(get_user_context)
):
    """Forecast maintenance demand for the fleet"""
    analyzer = TrendAnalyzer()
    return await analyzer.forecast_maintenance_demand(org_id, forecast_days)

@router.get("/organizations/{org_id}/best-performers")
async def get_best_performers(
    org_id: str,
    metric: str = 'oee',
    top_n: int = 5,
    user: UserContext = Depends(get_user_context)
):
    """Get top-performing locations"""
    analyzer = FleetAnalyzer()
    return await analyzer.identify_best_performers(org_id, metric, top_n)

@router.get("/organizations/{org_id}/underperformers")
async def get_underperformers(
    org_id: str,
    threshold: float = 0.7,
    user: UserContext = Depends(get_user_context)
):
    """Identify underperforming locations"""
    analyzer = FleetAnalyzer()
    return await analyzer.identify_underperformers(org_id, threshold)
```

## Visualization

### Executive Dashboard
```yaml
# Dashboard configuration
dashboard:
  title: "Fleet Overview"
  refresh_interval: 60s
  
  panels:
    - id: fleet_health
      title: "Fleet Health Score"
      type: gauge
      query: "SELECT AVG(oee) FROM fleet_metrics WHERE timestamp > NOW() - INTERVAL '24 hours'"
      thresholds:
        critical: 0.6
        warning: 0.75
        good: 0.85
    
    - id: location_map
      title: "Location Performance Map"
      type: map
      markers:
        - location_name
        - oee_score
        - device_count
        - alert_count
    
    - id: failure_trends
      title: "Failure Trends (30 days)"
      type: timeseries
      metrics:
        - total_failures
        - mtbf
      group_by: location
    
    - id: oee_comparison
      title: "OEE by Location"
      type: bar_chart
      metric: oee
      sort: desc
    
    - id: cost_analysis
      title: "Maintenance Cost by Location"
      type: stacked_area
      metrics:
        - planned_maintenance_cost
        - unplanned_maintenance_cost
        - downtime_cost
```

## Best Practices

### Data Collection
1. **Standardize metrics** across all locations
2. **Synchronize clocks** for accurate time-series analysis
3. **Use continuous aggregates** for performance
4. **Implement data quality checks**
5. **Regular backups** of fleet data

### Analytics
1. **Compare like-for-like** (similar device types, shift patterns)
2. **Account for seasonality** in trend analysis
3. **Use statistical significance tests**
4. **Regular calibration** of benchmarks
5. **Document assumptions** in analyses

### Reporting
1. **Executive summaries** with key metrics
2. **Location-specific** detailed reports
3. **Actionable insights** with recommendations
4. **Trend visualizations** for easy interpretation
5. **Regular cadence** (daily, weekly, monthly)

## Related Documentation

- [Multi-Tenant Architecture](MULTI_TENANT_ARCHITECTURE.md)
- [Data Persistence](DATA_PERSISTENCE.md)
- [Monitoring](MONITORING.md)
- [Cloud Integration](CLOUD_INTEGRATION.md)
- [API Documentation](API.md)
