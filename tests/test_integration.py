#!/usr/bin/env python3
"""
Integration test - tests GameState with simulated Client.txt

Simulates zone changes and verifies callbacks fire correctly.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import time
import threading
from game_state import GameState


def simulate_zone_changes(log_path: str):
    """Write zone changes to mock Client.txt"""
    # Use zone IDs (robust, unique identifiers)
    zones = [
        ("1_1_1", "Twilight Strand"),
        ("1_1_town", "Lioneye's Watch"),
        ("1_1_2", "The Coast"),
        ("1_1_3", "Mud Flats"),
        ("1_1_4_1", "Submerged Passage"),
        ("1_1_5", "The Ledge"),
        ("1_1_6", "The Climb"),
        ("1_1_7_1", "Lower Prison"),
        ("1_1_7_2", "Upper Prison"),  # Passive point
        ("1_1_8", "Prisoner's Gate"),
        ("1_1_9", "Ship Graveyard"),
        ("1_1_11_1", "Cavern of Wrath"),  # Passive point
        ("1_1_town", "Lioneye's Watch"),  # Back to town
        ("1_2_1", "Southern Forest"),  # Act 2
        ("1_2_town", "Forest Encampment"),
    ]

    print("Simulating zone changes...\n")
    time.sleep(2)  # Give monitor time to start

    for i, (zone_id, zone_name) in enumerate(zones):
        time.sleep(1)  # 1 second between zones
        level = 1 + i
        # Use actual PoE log format: "Generating level X area "zone_id" with seed..."
        line = f'2025/11/14 10:{10+i:02d}:00 12345678{i} 1186a8e1 [DEBUG Client 312] Generating level {level} area "{zone_id}" with seed 123456789\n'

        with open(log_path, 'a') as f:
            f.write(line)

        print(f"  [Writer] Wrote: {zone_id} ({zone_name})")


def main():
    """Test the integration"""
    print("=== Integration Test - GameState ===\n")

    # Create mock Client.txt
    test_log = "/tmp/test_client_integration.txt"
    with open(test_log, 'w') as f:
        f.write("2024/11/14 10:00:00 123456789 [INFO] Client version: 3.25.0\n")

    print(f"Created test log: {test_log}\n")

    # Create game state with explicit path
    game_state = GameState(client_txt_path=test_log)

    # Track events
    events = {
        'zones': [],
        'act_changes': [],
        'passive_points': []
    }

    def on_zone(entry):
        events['zones'].append(entry.zone_name)
        print(f"  ✓ Zone: {entry.zone_name} (Act {entry.act})")

    def on_act(old_act, new_act):
        events['act_changes'].append((old_act, new_act))
        print(f"  ★ Act changed: {old_act} → {new_act}")

    def on_passive(zone_name, total):
        events['passive_points'].append(total)
        print(f"  ⚡ Passive point in {zone_name}! Total: {total}")

    game_state.on_zone_change = on_zone
    game_state.on_act_change = on_act
    game_state.on_passive_point = on_passive

    # Start monitoring
    game_state.start()

    # Start simulator in background
    simulator = threading.Thread(target=simulate_zone_changes, args=(test_log,), daemon=True)
    simulator.start()

    # Wait for simulation to complete
    time.sleep(20)

    # Stop monitoring
    game_state.stop()

    # Verify results
    print("\n=== Test Results ===")
    print(f"Zones detected: {len(events['zones'])}/15")
    print(f"Act changes: {len(events['act_changes'])} (expected 1: Act 1 → 2)")
    print(f"Passive points: {len(events['passive_points'])} (expected 2)")

    # Get final state
    state = game_state.get_current_state()
    print(f"\nFinal state:")
    print(f"  Zone: {state['zone']}")
    print(f"  Act: {state['act']}")
    print(f"  Passive points: {state['passive_points']}")
    print(f"  Total zones: {state['zone_count']}")

    # Assertions
    assert len(events['zones']) == 15, f"Expected 15 zones, got {len(events['zones'])}"
    assert len(events['act_changes']) == 1, f"Expected 1 act change, got {len(events['act_changes'])}"
    assert len(events['passive_points']) == 2, f"Expected 2 passive points, got {len(events['passive_points'])}"
    assert state['act'] == 2, f"Expected Act 2, got {state['act']}"
    assert state['passive_points'] == 2, f"Expected 2 passive points, got {state['passive_points']}"

    print("\n✓ Integration test passed!")


if __name__ == "__main__":
    main()
