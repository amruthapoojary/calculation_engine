"""
spark/influx_writer.py
Writes calculation results to InfluxDB 2.0 using the Python client.
"""
import os
import sys
from typing import Dict, Any
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


class InfluxDBWriter:
    """
    Writes metrics and alert data to InfluxDB 2.0.
    Uses line protocol for efficient bulk writes.
    """
    
    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
    ):
        """
        Initialize InfluxDB connection.
        
        Args:
            url: InfluxDB server URL (e.g., "http://localhost:8086")
            token: API token with write permissions
            org: Organization name
            bucket: Bucket name
        """
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        
        try:
            self.client = InfluxDBClient(
                url=url,
                token=token,
                org=org,
                verify_ssl=False,
                timeout=10_000,
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            print(f"[InfluxDB] Connected to {url}, bucket '{bucket}'")
        except Exception as e:
            print(f"[InfluxDB] Connection failed: {e}")
            raise
    
    def write_results(self, process_result: Dict[str, Any], timestamp: int) -> bool:
        """
        Write complete calculation results to InfluxDB.
        Creates line protocol entries for metrics and alerts.
        
        Args:
            process_result: Output from CalculationEngine.process()
            timestamp: Unix timestamp in nanoseconds
        
        Returns:
            True if write successful, False otherwise
        """
        try:
            lines = []
            asset_id = process_result.get("asset_id", "unknown")

            # Write raw input readings so the dashboard can plot phase currents over time.
            input_metrics = process_result.get("input_metrics", {})
            if input_metrics:
                input_fields = []
                for field_name, field_value in input_metrics.items():
                    if field_value is None:
                        continue
                    input_fields.append(f"{field_name}={field_value}")

                if input_fields:
                    line = (
                        f"input_metrics,"
                        f"asset_id={asset_id} "
                        f"{','.join(input_fields)} "
                        f"{timestamp}"
                    )
                    lines.append(line)
            
            # Write calculated metrics
            metrics = process_result.get("metrics", {})
            for metric_name, metric_data in metrics.items():
                if metric_data.get("error"):
                    continue
                
                value = metric_data.get("value")
                if value is None:
                    continue
                
                # Line protocol: measurement,tags=values field=value timestamp
                line = (
                    f"calculated_metrics,"
                    f"asset_id={asset_id},"
                    f"metric={metric_name} "
                    f"value={value} "
                    f"{timestamp}"
                )
                lines.append(line)
            
            # Write alert statuses
            alerts = process_result.get("alerts", {})
            for metric_name, alert_data in alerts.items():
                status = alert_data.get("status", "UNKNOWN")
                value = alert_data.get("value")
                
                # Convert status to numeric for easier graphing
                status_value = {
                    "NORMAL": 0,
                    "ALERT": 1,
                    "WARNING": 2,
                    "ALARM": 3,
                    "N/A": -1,
                    "UNKNOWN": -1,
                }.get(status, -1)
                
                line = (
                    f"alert_status,"
                    f"asset_id={asset_id},"
                    f"metric={metric_name},"
                    f"status={status} "
                    f"value={status_value} "
                    f"{timestamp}"
                )
                lines.append(line)
                
                # Write alert value for reference
                if value is not None:
                    line = (
                        f"alert_value,"
                        f"asset_id={asset_id},"
                        f"metric={metric_name} "
                        f"value={value} "
                        f"{timestamp}"
                    )
                    lines.append(line)
            
            # Write worst overall status
            worst_status = process_result.get("worst_status", "NORMAL")
            worst_value = {
                "NORMAL": 0,
                "ALERT": 1,
                "WARNING": 2,
                "ALARM": 3,
            }.get(worst_status, 0)
            
            line = (
                f"overall_status,"
                f"asset_id={asset_id} "
                f"value={worst_value},status=\"{worst_status}\" "
                f"{timestamp}"
            )
            lines.append(line)
            
            # Batch write all lines
            if lines:
                write_string = "\n".join(lines)
                self.write_api.write(
                    bucket=self.bucket,
                    record=write_string,
                )
            
            return True
        
        except Exception as e:
            print(f"[InfluxDB] Write failed: {e}")
            return False
    
    def close(self):
        """Close InfluxDB connection."""
        try:
            self.client.close()
        except Exception as e:
            print(f"[InfluxDB] Close error: {e}")
