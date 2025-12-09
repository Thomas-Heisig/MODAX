"""Shared utility functions for MODAX tests"""
import statistics
from typing import List


def calculate_p95(times: List[float]) -> float:
    """
    Calculate the 95th percentile of a list of times.
    
    This function provides a consistent way to calculate P95 metrics
    across all test suites.
    
    Args:
        times: List of time measurements (in any unit)
        
    Returns:
        95th percentile value, or max value if insufficient data,
        or 0 if the list is empty
        
    Examples:
        >>> times = [1.0, 2.0, 3.0, 4.0, 5.0] * 20  # 100 samples
        >>> p95 = calculate_p95(times)
        >>> print(f"P95: {p95:.2f}")
        P95: 5.00
    """
    if not times:
        return 0.0
    
    if len(times) < 20:
        # Not enough data for reliable percentile, return max
        return max(times)
    
    # Using quantiles with n=100 returns 99 cut points (indices 0-98)
    # that divide the data into 100 equal-sized groups.
    # Index 94 represents the cut point where 95% of the data is below
    # and 5% is above, which is the 95th percentile.
    return statistics.quantiles(times, n=100)[94]


def calculate_p99(times: List[float]) -> float:
    """
    Calculate the 99th percentile of a list of times.
    
    Args:
        times: List of time measurements (in any unit)
        
    Returns:
        99th percentile value, or max value if insufficient data
    """
    if not times:
        return 0.0
    
    if len(times) < 100:
        return max(times)
    
    # Index 98 gives us the 99th percentile (0-indexed)
    return statistics.quantiles(times, n=100)[98]


def format_performance_stats(times: List[float], unit: str = "ms") -> str:
    """
    Format performance statistics in a human-readable way.
    
    Args:
        times: List of time measurements
        unit: Unit of measurement (default: "ms")
        
    Returns:
        Formatted string with avg, min, max, and P95
    """
    if not times:
        return f"No data (0 samples)"
    
    avg = statistics.mean(times)
    minimum = min(times)
    maximum = max(times)
    p95 = calculate_p95(times)
    
    return (f"Avg: {avg:.2f}{unit}, "
            f"Min: {minimum:.2f}{unit}, "
            f"Max: {maximum:.2f}{unit}, "
            f"P95: {p95:.2f}{unit}")
