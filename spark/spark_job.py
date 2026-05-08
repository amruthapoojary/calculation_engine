"""
spark/spark_job.py
Main Spark Streaming job that:
1. Reads from Kafka (energy-meter topic)
2. Uses CalculationEngine to compute metrics and alerts
3. Writes results to InfluxDB
"""
import os
import sys
import time
import json
import yaml
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, functions as F
from engine.calculator import CalculationEngine
from spark.influx_writer import InfluxDBWriter


def load_config(path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def create_spark_session(app_name: str = "EnergyCalculationEngine") -> SparkSession:
    """Create Spark session with Kafka dependencies."""
    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
        .config("spark.streaming.kafka.maxRatePerPartition", "1000")
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoint")
        .getOrCreate()
    )


def process_batch(batch_df, batch_id: int, config: dict, influx: InfluxDBWriter):
    """
    Process a single micro-batch from Kafka.
    
    Args:
        batch_df: DataFrame with Kafka messages for this batch
        batch_id: Batch sequence number
        config: Configuration dict from config.yaml
        influx: InfluxDBWriter instance
    """
    if batch_df.count() == 0:
        return
    
    # Initialize calculation engine with config
    engine = CalculationEngine(config)
    
    # Convert to Pandas for row-by-row processing
    try:
        rows = batch_df.collect()
    except Exception as e:
        print(f"[Spark] Error collecting batch {batch_id}: {e}")
        return
    
    print(f"\n[Batch {batch_id}] Processing {len(rows)} messages")
    
    for i, row in enumerate(rows):
        try:
            # Parse Kafka message
            kafka_value = json.loads(row.value)
            asset_id = kafka_value.get("asset_id", "unknown")
            timestamp = kafka_value.get("timestamp", int(time.time()))
            input_metrics = kafka_value.get("metrics", {})
            
            # Run calculation engine
            result = engine.process(input_metrics)
            worst_status = result.get("worst_status", "NORMAL")
            
            # Log result
            metrics_summary = {
                k: round(v["value"], 2) if isinstance(v.get("value"), float) else v.get("value")
                for k, v in result.get("metrics", {}).items()
                if not v.get("error")
            }
            alerts_summary = {
                k: v.get("status", "N/A")
                for k, v in result.get("alerts", {}).items()
            }
            
            print(
                f"  [{i+1}] asset={asset_id} | "
                f"metrics={metrics_summary} | "
                f"alerts={alerts_summary} | "
                f"worst={worst_status}"
            )
            
            # Write to InfluxDB
            timestamp_ns = timestamp * 1_000_000_000  # Convert to nanoseconds
            if not influx.write_results(result, timestamp_ns):
                print(f"    [ERROR] Failed to write to InfluxDB for {asset_id}")
        
        except json.JSONDecodeError as e:
            print(f"  [ERROR] Invalid JSON in batch {batch_id}, row {i}: {e}")
        except Exception as e:
            print(f"  [ERROR] Processing failed for batch {batch_id}, row {i}: {e}")


def main():
    """Main Spark Streaming job."""
    cfg = load_config()
    
    # Extract configuration
    kafka_servers = cfg["kafka"]["bootstrap_servers"]
    kafka_topic = cfg["kafka"]["topic"]
    
    influx_url = os.environ.get("INFLUX_URL", cfg["influxdb"]["url"])
    influx_token = os.environ.get("INFLUX_TOKEN", cfg["influxdb"]["token"])
    influx_org = cfg["influxdb"]["org"]
    influx_bucket = cfg["influxdb"]["bucket"]
    
    asset_id = cfg["asset"]["id"]
    asset_name = cfg["asset"]["name"]
    
    print("=" * 80)
    print(f"[Spark Job] Energy Calculation Engine")
    print(f"[Asset] {asset_name} ({asset_id})")
    print(f"[Kafka] Brokers: {kafka_servers}, Topic: {kafka_topic}")
    print(f"[InfluxDB] URL: {influx_url}, Bucket: {influx_bucket}")
    print("=" * 80)
    
    # Create Spark session
    spark = create_spark_session()
    
    # Initialize InfluxDB writer
    try:
        influx = InfluxDBWriter(
            url=influx_url,
            token=influx_token,
            org=influx_org,
            bucket=influx_bucket,
        )
    except Exception as e:
        print(f"[ERROR] InfluxDB initialization failed: {e}")
        sys.exit(1)
    
    try:
        # Read from Kafka
        df = (
            spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", kafka_servers)
            .option("subscribe", kafka_topic)
            .option("startingOffsets", "latest")
            .load()
        )
        
        # Cast value to string
        df = df.select(F.col("value").cast("string"))
        
        # Process each micro-batch
        query = (
            df.writeStream
            .foreachBatch(
                lambda batch_df, batch_id: process_batch(
                    batch_df, batch_id, cfg, influx
                )
            )
            .option("checkpointLocation", "/tmp/spark-checkpoint")
            .start()
        )
        
        print("\n[Spark] Streaming started. Waiting for data...")
        print("[Spark] Press Ctrl+C to stop.\n")
        
        query.awaitTermination()
    
    except KeyboardInterrupt:
        print("\n[Spark] Streaming stopped by user.")
    except Exception as e:
        print(f"[ERROR] Streaming error: {e}")
        raise
    finally:
        influx.close()
        spark.stop()
        print("[Spark] Session closed.")


if __name__ == "__main__":
    main()
