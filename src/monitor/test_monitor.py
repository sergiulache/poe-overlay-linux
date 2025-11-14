#!/usr/bin/env python3
"""
Test script for Client.txt monitor

Creates a mock Client.txt and writes test zone changes
"""

import time
import threading
from pathlib import Path
from client_log import ClientLogMonitor


def create_test_log():
    """Create test Client.txt with some initial content"""
    test_log = Path("/tmp/test_client.txt")
    test_log.write_text("""2024/11/14 10:00:00 123456789 [INFO] Client version: 3.25.0
2024/11/14 10:01:00 123456790 [INFO] Connecting to instance server...
""")
    return str(test_log)


def simulate_zone_changes(log_path: str):
    """Simulate zone changes by appending to log file"""
    zones = [
        "Lioneye's Watch",
        "The Coast",
        "The Mud Flats",
        "The Submerged Passage",
        "The Flooded Depths",
        "The Ledge",
        "The Climb"
    ]

    print("\nSimulating zone changes (writing to log)...\n")
    time.sleep(2)  # Give monitor time to start

    for i, zone in enumerate(zones):
        time.sleep(2)  # Wait 2 seconds between zones
        level = 1 + i
        line = f'2024/11/14 10:{10+i:02d}:00 12345678{i} [INFO] : Generating level {level} area "{zone}"\n'

        with open(log_path, 'a') as f:
            f.write(line)

        print(f"  [Writer] Wrote: {zone}")


def main():
    print("=== Client.txt Monitor Test ===\n")

    # Create test log file
    test_log = create_test_log()
    print(f"Created test log: {test_log}\n")

    # Create monitor with explicit path
    monitor = ClientLogMonitor(client_txt_path=test_log)

    # Track zones detected
    zones_detected = []

    def on_zone(zone_name: str):
        zones_detected.append(zone_name)
        print(f"  ✓ [Monitor] Detected: {zone_name}")

    monitor.on_zone_change(on_zone)

    # Start zone simulation in background thread
    simulator = threading.Thread(target=simulate_zone_changes, args=(test_log,), daemon=True)
    simulator.start()

    # Start monitoring (will run until we stop it)
    try:
        # Run for 20 seconds
        monitor_thread = threading.Thread(target=monitor.start, daemon=True)
        monitor_thread.start()

        # Wait for simulation to complete
        time.sleep(20)

        monitor.stop()

        # Show results
        print(f"\n=== Test Complete ===")
        expected = 7
        print(f"Zones detected: {len(zones_detected)}/{expected}")
        print(f"Zones: {', '.join(zones_detected)}")

        # Assert for automated testing
        assert len(zones_detected) == expected, f"Expected {expected} zones, got {len(zones_detected)}"
        print("\n✓ Test passed!")

    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        monitor.stop()


if __name__ == "__main__":
    main()
