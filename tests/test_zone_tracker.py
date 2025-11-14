#!/usr/bin/env python3
"""
Comprehensive test suite for ZoneTracker

Tests zone tracking, act detection, passive points, and edge cases.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zone_tracker import ZoneTracker, ZoneEntry
from data_loader import GameDataLoader


def main():
    """Run comprehensive zone tracker tests"""
    print("=== Zone Tracker Comprehensive Test Suite ===\n")

    # Test 1: Basic zone tracking
    print("Test 1: Basic zone tracking...")
    loader = GameDataLoader()
    tracker = ZoneTracker(loader)

    entry = tracker.enter_zone("Twilight Strand")
    assert entry is not None, "Should find Twilight Strand"
    assert entry.zone_name == "Twilight Strand"
    assert entry.act == 1
    assert tracker.current_act == 1
    assert len(tracker.zone_history) == 1
    print("  ✓ Basic zone entry works")

    # Test 2: Act progression
    print("\nTest 2: Act progression detection...")
    tracker.reset()

    # Act 1 final zone
    tracker.enter_zone("Cavern of Wrath")
    assert tracker.current_act == 1

    # Act 2 first zone - should trigger act change
    act_changed = False
    def on_act(old, new):
        nonlocal act_changed
        act_changed = True
        assert old == 1 and new == 2

    tracker.on_act_change(on_act)
    tracker.enter_zone("Southern Forest")

    assert act_changed, "Act change callback should fire"
    assert tracker.current_act == 2
    print("  ✓ Act progression detected")

    # Test 3: Passive point calculation
    print("\nTest 3: Passive point calculation...")
    tracker.reset()

    passive_count = 0
    def on_passive(zone, total):
        nonlocal passive_count
        passive_count += 1

    tracker.on_passive_point(on_passive)

    # Progress through Act 1 quest zones
    tracker.enter_zone("Twilight Strand")
    tracker.enter_zone("Lioneye's Watch")
    tracker.enter_zone("The Coast")
    tracker.enter_zone("Mud Flats")
    tracker.enter_zone("Submerged Passage")
    tracker.enter_zone("The Ledge")
    tracker.enter_zone("The Climb")
    tracker.enter_zone("Lower Prison")

    # Upper Prison - first passive point
    tracker.enter_zone("Upper Prison")
    assert tracker.passive_points == 1, "Should have 1 passive point after Brutus"
    assert passive_count == 1

    tracker.enter_zone("Prisoner's Gate")
    tracker.enter_zone("Ship Graveyard")

    # Cavern of Wrath - second passive point
    tracker.enter_zone("Cavern of Wrath")
    assert tracker.passive_points == 2, "Should have 2 passive points after Merveil"
    assert passive_count == 2

    print("  ✓ Passive points calculated correctly (2/2 for Act 1)")

    # Test 4: Revisiting zones (no double passive points)
    print("\nTest 4: Revisiting zones...")
    initial_points = tracker.passive_points

    # Revisit passive zone - should not grant point again
    tracker.enter_zone("Upper Prison")
    assert tracker.passive_points == initial_points, "Should not double-count passive points"
    assert passive_count == 2, "Callback should not fire again"

    print("  ✓ No double-counting on revisits")

    # Test 5: Town backtracking
    print("\nTest 5: Town backtracking...")
    tracker.reset()

    # Progress to Act 2
    tracker.enter_zone("Twilight Strand")
    tracker.enter_zone("Lioneye's Watch")  # Act 1 town
    tracker.enter_zone("The Coast")
    tracker.enter_zone("Mud Flats")
    tracker.enter_zone("Submerged Passage")
    tracker.enter_zone("The Ledge")
    tracker.enter_zone("The Climb")
    tracker.enter_zone("Lower Prison")
    tracker.enter_zone("Upper Prison")
    tracker.enter_zone("Prisoner's Gate")
    tracker.enter_zone("Ship Graveyard")
    tracker.enter_zone("Cavern of Wrath")

    # Enter Act 2
    tracker.enter_zone("Southern Forest")
    tracker.enter_zone("Forest Encampment")  # Act 2 town
    assert tracker.current_act == 2

    # Backtrack to Act 1 town - should stay in Act 2
    tracker.enter_zone("Lioneye's Watch")
    assert tracker.current_act == 2, "Should not regress act when backtracking to town"

    # Return to Act 2
    tracker.enter_zone("Forest Encampment")
    assert tracker.current_act == 2

    print("  ✓ Town backtracking handled correctly")

    # Test 6: Zone history tracking
    print("\nTest 6: Zone history tracking...")
    tracker.reset()

    zones = ["Twilight Strand", "Lioneye's Watch", "The Coast", "Mud Flats"]
    for zone in zones:
        tracker.enter_zone(zone)

    assert len(tracker.zone_history) == 4
    assert len(tracker.visited_zones) == 4

    recent = tracker.get_recent_zones(2)
    assert len(recent) == 2
    assert recent[0].zone_name == "The Coast"
    assert recent[1].zone_name == "Mud Flats"

    act1_zones = tracker.get_act_zones_visited(1)
    assert len(act1_zones) == 4

    print("  ✓ Zone history tracking works")

    # Test 7: Multi-act progression
    print("\nTest 7: Multi-act progression (Act 1 → 2 → 3)...")
    # Create a fresh tracker to avoid callback conflicts
    tracker = ZoneTracker(loader)

    # Act 1 → 2
    tracker.enter_zone("Cavern of Wrath")
    assert tracker.current_act == 1

    tracker.enter_zone("Southern Forest")
    assert tracker.current_act == 2

    # Act 2 → 3
    tracker.enter_zone("Sarn Encampment")  # Act 3 town
    assert tracker.current_act == 3

    print("  ✓ Multi-act progression works")

    # Test 8: Unknown zone handling
    print("\nTest 8: Unknown zone handling...")
    tracker.reset()

    entry = tracker.enter_zone("Completely Made Up Zone Name")
    assert entry is None, "Should return None for unknown zones"
    assert len(tracker.zone_history) == 0, "Should not add unknown zones to history"

    print("  ✓ Unknown zones handled gracefully")

    # Test 9: Reset functionality
    print("\nTest 9: Reset functionality...")
    tracker.reset()

    # Add some data
    tracker.enter_zone("Twilight Strand")
    tracker.enter_zone("Lioneye's Watch")

    # Reset
    tracker.reset()

    assert len(tracker.zone_history) == 0
    assert tracker.current_zone is None
    assert tracker.current_act == 1
    assert tracker.passive_points == 0
    assert len(tracker.visited_zones) == 0

    print("  ✓ Reset clears all state")

    # Test 10: Realistic full Act 1 playthrough
    print("\nTest 10: Realistic full Act 1 playthrough...")
    tracker.reset()

    zone_changes = 0
    def count_zones(entry):
        nonlocal zone_changes
        zone_changes += 1

    tracker.on_zone_change(count_zones)

    # Full Act 1 path (typical speedrun route)
    act1_playthrough = [
        "Twilight Strand",
        "Lioneye's Watch",
        "The Coast",
        "Mud Flats",
        "Submerged Passage",
        "Flooded Depths",  # Quest
        "Submerged Passage",  # Back
        "The Ledge",
        "The Climb",
        "Lower Prison",
        "Upper Prison",  # Passive point
        "Prisoner's Gate",
        "Ship Graveyard",
        "Cavern of Wrath",  # Passive point
        "Lioneye's Watch",  # Return to town
    ]

    for zone in act1_playthrough:
        entry = tracker.enter_zone(zone)
        if entry:
            assert entry.act == 1, f"Zone {zone} should be in Act 1"

    assert zone_changes == len(act1_playthrough), f"Should track all {len(act1_playthrough)} zone changes"
    assert tracker.passive_points == 2, "Should have 2 passive points after full Act 1"
    assert tracker.current_act == 1

    print(f"  ✓ Full Act 1 playthrough: {len(act1_playthrough)} zones, 2 passive points")

    # Summary
    print("\n=== All Tests Passed ===")
    print("Zone tracking: ✓")
    print("Act detection: ✓")
    print("Passive points: ✓")
    print("Edge cases: ✓")
    print("\n✓ Zone tracker fully tested and working!")


if __name__ == "__main__":
    main()
