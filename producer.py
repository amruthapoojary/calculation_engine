"""
producer.py
Kafka producer that simulates energy meter readings for motor1.
Generates random 3-phase current data (I_R, I_Y, I_B), voltage, and power factor.
"""
import json
import os
import random
import time
import yaml
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable


def load_config(path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def make_producer(bootstrap_servers: str, retries: int = 10) -> KafkaProducer:
    """
    Create Kafka producer with exponential backoff retry logic.
    Ensures producer doesn't fail silently if Kafka isn't ready yet.
    """
    for attempt in range(1, retries + 1):
        try:
            return KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=3,
                acks=1,  # wait for broker ack
            )
        except NoBrokersAvailable:
            wait = min(2 ** attempt, 30)
            print(
                f"[Producer] Kafka not ready (attempt {attempt}/{retries}), "
                f"retrying in {wait}s …"
            )
            time.sleep(wait)
    raise RuntimeError("Could not connect to Kafka after multiple retries.")


def generate_reading(asset_id: str = "motor1") -> dict:
    """
    Generate simulated 3-phase energy meter reading for Motor 1.
    
    Normal operation:
    - I_R, I_Y, I_B: 10-20 A (balanced)
    - I_B occasionally 0 A to simulate phase imbalance
    
    Returns:
        Dict with timestamp, asset_id, and input metrics for calculation engine
    """
    # Simulate occasional phase imbalance (5% chance of I_B = 0)
    i_b = 0.0 if random.random() < 0.05 else random.uniform(10, 20)
    
    return {
        "asset_id": asset_id,
        "timestamp": int(time.time()),
        "metrics": {
            "I_R": round(random.uniform(10, 20), 3),      # Red phase current (A)
            "I_Y": round(random.uniform(10, 20), 3),      # Yellow phase current (A)
            "I_B": round(i_b, 3),                         # Blue phase current (A)
            "voltage": 415.0,                              # Line-to-neutral (V)
            "power_factor": round(random.uniform(0.8, 1.0), 3),  # Power factor
        },
    }


def main():
    """Main producer loop."""
    cfg = load_config()
    topic = cfg["kafka"]["topic"]
    servers = cfg["kafka"]["bootstrap_servers"]
    asset_id = cfg["asset"]["id"]
    interval_s = float(os.environ.get("PRODUCER_INTERVAL", "1.0"))

    producer = make_producer(servers)
    print(
        f"[Producer] Connected to Kafka: {servers}"
    )
    print(
        f"[Producer] Sending '{asset_id}' readings to topic '{topic}' "
        f"every {interval_s}s. Ctrl+C to stop."
    )

    sent = 0
    try:
        while True:
            reading = generate_reading(asset_id)
            future = producer.send(topic, reading)
            try:
                future.get(timeout=5)  # surface send errors immediately
                sent += 1
                if sent % 10 == 0:
                    metrics = reading["metrics"]
                    print(
                        f"[Producer] {sent} messages sent. "
                        f"Last: I_R={metrics['I_R']}, I_Y={metrics['I_Y']}, "
                        f"I_B={metrics['I_B']}, Voltage={metrics['voltage']}, "
                        f"PF={metrics['power_factor']}"
                    )
            except KafkaError as exc:
                print(f"[Producer] Send failed: {exc}")
            time.sleep(interval_s)
    except KeyboardInterrupt:
        print(f"\n[Producer] Stopped after {sent} messages.")
    finally:
        producer.flush()
        producer.close()
        print("[Producer] Connection closed.")


if __name__ == "__main__":
    main()
