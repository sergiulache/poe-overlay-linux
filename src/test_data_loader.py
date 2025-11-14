#!/usr/bin/env python3
"""
Test script for GameDataLoader

Validates that all JSON data loads correctly and access methods work.
"""

from data_loader import GameDataLoader


def main():
    """Test the data loader"""
    print("=== Game Data Loader Test ===\n")

    # Create loader
    loader = GameDataLoader()

    # Test 1: Areas data loads
    print("Test 1: Loading areas data...")
    areas = loader.areas
    assert isinstance(areas, list), "Areas should be a list"
    assert len(areas) > 0, "Areas should not be empty"
    print(f"  ✓ Loaded {len(areas)} acts")

    # Test 2: Each act has zones
    print("\nTest 2: Validating act zone data...")
    for act_num in range(1, len(areas) + 1):
        act_zones = loader.get_act_areas(act_num)
        assert isinstance(act_zones, list), f"Act {act_num} zones should be a list"
        assert len(act_zones) > 0, f"Act {act_num} should have zones"
        print(f"  ✓ Act {act_num}: {len(act_zones)} zones")

    # Test 3: Zone objects have required fields
    print("\nTest 3: Validating zone object structure...")
    first_zone = loader.get_act_areas(1)[0]
    assert 'id' in first_zone, "Zone should have 'id' field"
    assert 'name' in first_zone, "Zone should have 'name' field"
    print(f"  ✓ Zone structure valid: {first_zone}")

    # Test 4: Guide data loads
    print("\nTest 4: Loading guide data...")
    guide = loader.guide
    assert isinstance(guide, list), "Guide should be a list"
    assert len(guide) > 0, "Guide should not be empty"
    print(f"  ✓ Loaded guide for {len(guide)} acts")

    # Test 5: Each act has guide steps
    print("\nTest 5: Validating act guide data...")
    for act_num in range(1, len(guide) + 1):
        act_guide = loader.get_act_guide(act_num)
        assert isinstance(act_guide, list), f"Act {act_num} guide should be a list"
        # Guide can be empty for some acts
        print(f"  ✓ Act {act_num}: {len(act_guide)} guide steps")

    # Test 6: Gems data loads
    print("\nTest 6: Loading gems data...")
    gems = loader.gems
    assert isinstance(gems, dict), "Gems should be a dict"
    assert '_quests' in gems, "Gems should have '_quests' key"
    quest_count = len(gems['_quests'])
    print(f"  ✓ Loaded gems data with {quest_count} quests")

    # Test 7: Zone name lookup
    print("\nTest 7: Testing zone name lookup...")
    test_zones = [
        "Lioneye's Watch",
        "The Coast",
        "Mud Flats",  # No "The" prefix in actual data
        "Highgate"  # Act 4/9 town
    ]
    for zone_name in test_zones:
        zone = loader.find_zone_by_name(zone_name)
        assert zone is not None, f"Zone '{zone_name}' should have been found"
        print(f"  ✓ Found '{zone_name}': {zone['id']}")

    # Test 8: Invalid act number handling
    print("\nTest 8: Testing error handling...")
    try:
        loader.get_act_areas(999)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  ✓ Invalid act error handled: {e}")

    # Summary
    print("\n=== All Tests Passed ===")
    print(f"Areas: {len(loader.areas)} acts")
    print(f"Guide: {len(loader.guide)} acts")
    print(f"Gems: {len(loader.gems.get('_quests', {}))} quests")
    print("\n✓ Data loader fully functional!")


if __name__ == "__main__":
    main()
