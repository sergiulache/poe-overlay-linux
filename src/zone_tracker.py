#!/usr/bin/env python3
"""
Zone tracking and game state management for Path of Exile

Tracks zone changes, determines current act, and calculates progression.
"""

from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime
from data_loader import GameDataLoader


@dataclass
class ZoneEntry:
    """Represents a zone visit"""
    zone_id: str
    zone_name: str
    act: int
    timestamp: datetime

    def __repr__(self):
        return f"ZoneEntry({self.zone_name}, act={self.act}, id={self.zone_id})"


class ZoneTracker:
    """
    Tracks zone changes and game progression

    Maintains zone history, detects act changes, and tracks game state.
    """

    # Passive point quest zones by act (simplified for MVP)
    # Format: {act: [zone_ids that give passive points]}
    PASSIVE_ZONES = {
        1: ["1_1_7_2", "1_1_11_1"],  # Upper Prison (Brutus), Cavern of Wrath (Merveil)
        2: ["1_2_10_3", "1_2_14_1"],  # Weaver's Chambers, Ancient Pyramid
        3: ["1_3_13_2", "1_3_15_2"],  # Piety fight, Sceptre of God
        4: ["1_4_3_2", "1_4_4_2"],    # Kaom/Daresso, Malachai
        5: ["1_5_3", "1_5_4"],        # Control Blocks, Innocence
        6: ["1_6_10_2", "1_6_30_4"],  # Shavronne/Maligaro, Brine King
        7: ["1_7_7_2", "1_7_10_3"],   # Maligaro, Kishara
        8: ["1_8_10_1", "1_8_12_3"],  # Yugul, Solaris/Lunaris
        9: ["1_9_10_2", "1_9_13"],    # Trinity fight, The Rotting Core
        10: ["1_10_9", "1_10_11"],    # Avarius, Kitava
    }

    def __init__(self, data_loader: GameDataLoader):
        """
        Initialize zone tracker

        Args:
            data_loader: GameDataLoader instance for zone data
        """
        self.data_loader = data_loader
        self.zone_history: List[ZoneEntry] = []
        self.current_zone: Optional[ZoneEntry] = None
        self.current_act: int = 1
        self.passive_points: int = 0
        self.visited_zones: set = set()
        self.completed_passive_zones: set = set()

        # Callbacks
        self.callbacks = {
            'zone_change': [],
            'act_change': [],
            'passive_point': []
        }

    def on_zone_change(self, callback: Callable[[ZoneEntry], None]):
        """Register callback for zone changes"""
        self.callbacks['zone_change'].append(callback)

    def on_act_change(self, callback: Callable[[int, int], None]):
        """Register callback for act changes (old_act, new_act)"""
        self.callbacks['act_change'].append(callback)

    def on_passive_point(self, callback: Callable[[str, int], None]):
        """Register callback for passive point gains (zone_name, total_points)"""
        self.callbacks['passive_point'].append(callback)

    def _find_zone_in_act_range(self, zone_name: str, start_act: int, end_act: int) -> Optional[Dict]:
        """
        Find a zone within a specific act range

        Args:
            zone_name: Zone name to find
            start_act: Starting act (inclusive)
            end_act: Ending act (inclusive)

        Returns:
            Zone data dict if found, None otherwise
        """
        for act in range(start_act, end_act + 1):
            if act < 1 or act > len(self.data_loader.areas):
                continue

            act_zones = self.data_loader.get_act_areas(act)
            for zone in act_zones:
                if zone['name'] == zone_name:
                    return zone
                if 'map_name' in zone and zone['map_name'] == zone_name:
                    return zone

        return None

    def _search_all_acts_by_proximity(self, zone_name: str) -> Optional[Dict]:
        """
        Search all acts for a zone, prioritizing acts closest to current_act.
        Handles duplicate zone names (e.g., Solaris Temple in Acts 3 & 8).

        Args:
            zone_name: Zone name to find

        Returns:
            Zone data dict if found, None otherwise
        """
        total_acts = len(self.data_loader.areas)

        # Search in order of distance from current act
        # Distance 0 (current), 1 (±1), 2 (±2), etc.
        for distance in range(total_acts):
            # Try act above current
            act_above = self.current_act + distance
            if act_above <= total_acts:
                result = self._find_zone_in_act_range(zone_name, act_above, act_above)
                if result:
                    return result

            # Try act below current (skip distance 0 to avoid duplicate)
            if distance > 0:
                act_below = self.current_act - distance
                if act_below >= 1:
                    result = self._find_zone_in_act_range(zone_name, act_below, act_below)
                    if result:
                        return result

        return None

    def enter_zone(self, zone_name: str) -> Optional[ZoneEntry]:
        """
        Process entering a new zone

        Args:
            zone_name: Name of zone being entered

        Returns:
            ZoneEntry if zone was found and tracked, None otherwise
        """
        # Find zone in data, prioritizing current/nearby acts
        # Search strategy:
        # 1. Current act
        # 2. Next 2 acts (progression)
        # 3. Previous act (backtracking)
        # 4. Global search (fallback)
        # Note: Try exact name first, then without "The " prefix if present

        zone_data = self._find_zone_in_act_range(zone_name, self.current_act, self.current_act)

        if not zone_data:
            # Try next acts (progression)
            zone_data = self._find_zone_in_act_range(
                zone_name,
                self.current_act + 1,
                min(self.current_act + 2, len(self.data_loader.areas))
            )

        if not zone_data and self.current_act > 1:
            # Try previous act (backtracking)
            zone_data = self._find_zone_in_act_range(zone_name, self.current_act - 1, self.current_act - 1)

        if not zone_data:
            # Fallback: search all acts, prioritizing closest to current act
            # This handles duplicate zone names (e.g., Solaris Temple in Act 3 & 8)
            zone_data = self._search_all_acts_by_proximity(zone_name)

        if not zone_data and zone_name.startswith("The "):
            # Try without "The " prefix (PoE data is inconsistent)
            # e.g., "The Submerged Passage" -> "Submerged Passage"
            normalized_name = zone_name[4:]
            zone_data = self._search_all_acts_by_proximity(normalized_name)
            if zone_data:
                zone_name = normalized_name  # Use normalized name for tracking

        if not zone_data:
            print(f"Warning: Unknown zone '{zone_name}'")
            return None

        zone_id = zone_data['id']

        # Determine act from zone (use current act progression logic)
        zone_act = self._determine_act(zone_id)

        # Create zone entry
        entry = ZoneEntry(
            zone_id=zone_id,
            zone_name=zone_name,
            act=zone_act,
            timestamp=datetime.now()
        )

        # Check for passive point (using O(1) set lookup)
        if self._is_passive_zone(zone_id) and zone_id not in self.completed_passive_zones:
            self.passive_points += 1
            self.completed_passive_zones.add(zone_id)
            # Fire callback after updating points
            for callback in self.callbacks['passive_point']:
                callback(zone_name, self.passive_points)

        # Update state
        old_act = self.current_act
        self.current_zone = entry
        self.zone_history.append(entry)
        self.visited_zones.add(zone_id)

        # Check for act change
        if zone_act != old_act:
            self.current_act = zone_act
            for callback in self.callbacks['act_change']:
                callback(old_act, zone_act)

        # Fire zone change callbacks
        for callback in self.callbacks['zone_change']:
            callback(entry)

        return entry

    def _determine_act(self, zone_id: str) -> int:
        """
        Determine which act a zone belongs to based on ID and current progression

        Zone IDs have format: {difficulty}_{act}_{zone}
        e.g., "1_1_2" = Normal difficulty, Act 1, zone 2

        Args:
            zone_id: Zone ID from areas.json

        Returns:
            Act number (1-10)
        """
        # Parse act from zone ID
        parts = zone_id.split('_')
        if len(parts) >= 2:
            try:
                zone_act = int(parts[1])

                # Act progression: can only go forward or stay same
                # (except for hideout/special zones which we ignore for now)
                if zone_act >= self.current_act:
                    return zone_act
                else:
                    # Revisiting old zone - keep current act
                    return self.current_act
            except ValueError:
                pass

        # Fallback: keep current act
        return self.current_act

    def _is_passive_zone(self, zone_id: str) -> bool:
        """Check if a zone gives passive points"""
        for act_zones in self.PASSIVE_ZONES.values():
            if zone_id in act_zones:
                return True
        return False

    def get_act_zones_visited(self, act: int) -> List[ZoneEntry]:
        """Get all zones visited in a specific act"""
        return [entry for entry in self.zone_history if entry.act == act]

    def get_recent_zones(self, count: int = 10) -> List[ZoneEntry]:
        """Get the most recent N zones"""
        return self.zone_history[-count:]

    def reset(self):
        """Reset all tracking state"""
        self.zone_history.clear()
        self.current_zone = None
        self.current_act = 1
        self.passive_points = 0
        self.visited_zones.clear()
        self.completed_passive_zones.clear()


def main():
    """Test the zone tracker"""
    print("=== Zone Tracker Test ===\n")

    # Load data
    loader = GameDataLoader()
    tracker = ZoneTracker(loader)

    # Register callbacks
    def on_zone(entry: ZoneEntry):
        print(f"  → Zone: {entry.zone_name} (Act {entry.act})")

    def on_act(old_act: int, new_act: int):
        print(f"  ★ Act changed: {old_act} → {new_act}")

    def on_passive(zone_name: str, total: int):
        print(f"  ⚡ Passive point earned in {zone_name}! Total: {total}")

    tracker.on_zone_change(on_zone)
    tracker.on_act_change(on_act)
    tracker.on_passive_point(on_passive)

    # Simulate Act 1 progression
    print("Simulating Act 1 progression...\n")
    act1_zones = [
        "Twilight Strand",
        "Lioneye's Watch",
        "The Coast",
        "Mud Flats",
        "Submerged Passage",
        "The Ledge",
        "The Climb",
        "Lower Prison",
        "Upper Prison",  # Passive point (Brutus)
        "Prisoner's Gate",
        "Ship Graveyard",
        "Cavern of Wrath"  # Passive point (Merveil)
    ]

    for zone in act1_zones:
        tracker.enter_zone(zone)

    # Simulate Act 2 start
    print("\nEntering Act 2...\n")
    tracker.enter_zone("Southern Forest")
    tracker.enter_zone("Forest Encampment")

    # Show summary
    print("\n=== Summary ===")
    print(f"Current Act: {tracker.current_act}")
    print(f"Current Zone: {tracker.current_zone.zone_name if tracker.current_zone else 'None'}")
    print(f"Total Zones: {len(tracker.zone_history)}")
    print(f"Passive Points: {tracker.passive_points}")
    print(f"Recent zones: {[z.zone_name for z in tracker.get_recent_zones(5)]}")

    print("\n✓ Zone tracker working!")


if __name__ == "__main__":
    main()
