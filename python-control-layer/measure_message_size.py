#!/usr/bin/env python3
"""
Message Size Measurement Utility

Measures and compares JSON vs Protobuf message sizes for MQTT optimization analysis.
Helps determine if Protobuf migration is beneficial for your deployment.

Usage:
    python measure_message_size.py
"""

import json
import sys
from typing import Dict


def create_sample_sensor_data() -> Dict:
    """Create a representative sensor data message"""
    return {
        "timestamp": 1701965432000,
        "device_id": "device_001",
        "motor_currents": [5.2, 5.3],
        "vibration": {
            "x": 1.2,
            "y": 1.1,
            "z": 0.9,
            "magnitude": 2.1
        },
        "temperatures": [45.5, 46.2]
    }


def create_sample_safety_status() -> Dict:
    """Create a representative safety status message"""
    return {
        "timestamp": 1701965432000,
        "device_id": "device_001",
        "emergency_stop": False,
        "door_closed": True,
        "overload_detected": False,
        "temperature_ok": True
    }


def create_sample_ai_analysis() -> Dict:
    """Create a representative AI analysis message"""
    return {
        "timestamp": 1701965432000,
        "device_id": "device_001",
        "anomaly_detected": False,
        "anomaly_score": 0.15,
        "anomaly_description": "All parameters within normal range",
        "predicted_wear_level": 0.23,
        "estimated_remaining_hours": 8640,
        "recommendations": [
            "Continue normal operation",
            "Schedule maintenance in 30 days"
        ],
        "confidence": 0.92
    }


def measure_json_size(data: Dict) -> int:
    """Measure JSON serialized size"""
    return len(json.dumps(data))


def calculate_bandwidth(message_size: int, frequency_hz: float) -> float:
    """Calculate bandwidth in bytes per second"""
    return message_size * frequency_hz


def format_bytes(bytes_value: float) -> str:
    """Format bytes as human-readable string"""
    if bytes_value < 1024:
        return f"{bytes_value:.0f} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.2f} KB"
    else:
        return f"{bytes_value / (1024 * 1024):.2f} MB"


def print_separator():
    """Print a visual separator"""
    print("=" * 80)


def analyze_message_type(name: str, data: Dict, frequency_hz: float):
    """Analyze a message type and print results"""
    print(f"\n{name}")
    print("-" * 80)

    # JSON measurements
    json_size = measure_json_size(data)
    json_bandwidth = calculate_bandwidth(json_size, frequency_hz)

    print(f"JSON Message Size:        {json_size} bytes")
    print(f"Frequency:                {frequency_hz} Hz")
    print(f"Bandwidth (per device):   {format_bytes(json_bandwidth)}/s")

    # Estimated Protobuf size (typically 60-70% smaller)
    estimated_protobuf_size = int(json_size * 0.35)
    estimated_protobuf_bandwidth = calculate_bandwidth(
        estimated_protobuf_size, frequency_hz)

    print(f"\nEstimated Protobuf Size:  {estimated_protobuf_size} bytes "
          f"({100 * (json_size - estimated_protobuf_size) / json_size:.0f}% smaller)")
    print(f"Estimated Bandwidth:      {format_bytes(estimated_protobuf_bandwidth)}/s")

    savings = json_bandwidth - estimated_protobuf_bandwidth
    print(f"Bandwidth Savings:        {format_bytes(savings)}/s per device")

    return {
        'json_size': json_size,
        'json_bandwidth': json_bandwidth,
        'protobuf_size': estimated_protobuf_size,
        'protobuf_bandwidth': estimated_protobuf_bandwidth,
        'savings': savings
    }


def main():
    """Main analysis function"""
    print_separator()
    print("MODAX MQTT Message Size Analysis")
    print_separator()

    # Configuration
    num_devices = 4  # Typical deployment
    sensor_frequency = 10  # Hz
    safety_frequency = 20  # Hz
    ai_frequency = 0.1  # Hz (once every 10 seconds)

    # Analyze each message type
    sensor_results = analyze_message_type(
        "Sensor Data Messages",
        create_sample_sensor_data(),
        sensor_frequency
    )

    safety_results = analyze_message_type(
        "Safety Status Messages",
        create_sample_safety_status(),
        safety_frequency
    )

    ai_results = analyze_message_type(
        "AI Analysis Messages",
        create_sample_ai_analysis(),
        ai_frequency
    )

    # Calculate totals for deployment
    print_separator()
    print(f"\nTotal System Analysis (with {num_devices} devices)")
    print("-" * 80)

    total_json_bandwidth = (
        sensor_results['json_bandwidth'] * num_devices +
        safety_results['json_bandwidth'] * num_devices +
        ai_results['json_bandwidth'] * num_devices
    )

    total_protobuf_bandwidth = (
        sensor_results['protobuf_bandwidth'] * num_devices +
        safety_results['protobuf_bandwidth'] * num_devices +
        ai_results['protobuf_bandwidth'] * num_devices
    )

    print(f"Total JSON Bandwidth:      {format_bytes(total_json_bandwidth)}/s")
    print(f"Total Protobuf Bandwidth:  {format_bytes(total_protobuf_bandwidth)}/s")
    print(f"Total Savings:             {format_bytes(total_json_bandwidth - total_protobuf_bandwidth)}/s")
    print(f"Reduction:                 {100 * (total_json_bandwidth - total_protobuf_bandwidth) / total_json_bandwidth:.1f}%")

    # Per day calculations
    seconds_per_day = 86400
    json_per_day = total_json_bandwidth * seconds_per_day
    protobuf_per_day = total_protobuf_bandwidth * seconds_per_day

    print(f"\nDaily Bandwidth Usage:")
    print(f"JSON:                      {format_bytes(json_per_day)}/day")
    print(f"Protobuf (estimated):      {format_bytes(protobuf_per_day)}/day")
    print(f"Daily Savings:             {format_bytes(json_per_day - protobuf_per_day)}/day")

    # Recommendations
    print_separator()
    print("\nRecommendations:")
    print("-" * 80)

    if total_json_bandwidth < 10000:  # < 10 KB/s
        print("✓ Current JSON implementation is suitable for this deployment.")
        print("✓ Bandwidth usage is low and network should handle it easily.")
        print("○ Consider Protobuf if scaling to >10 devices.")
    elif total_json_bandwidth < 50000:  # < 50 KB/s
        print("○ Current JSON usage is moderate.")
        print("○ Consider Protobuf migration if:")
        print("  - Using cellular/metered network")
        print("  - Planning to scale to more devices")
        print("  - Battery life is a concern")
    else:  # >= 50 KB/s
        print("! High bandwidth usage detected.")
        print("! Strongly recommend Protobuf migration to:")
        print("  - Reduce network load by ~65%")
        print("  - Improve system scalability")
        print("  - Extend battery life on field devices")

    print_separator()
    print("\nFor Protobuf migration steps, see: docs/MQTT_OPTIMIZATION.md")
    print_separator()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during analysis: {e}", file=sys.stderr)
        sys.exit(1)
