#!/usr/bin/env python3
"""
Data loader for Path of Exile game data (zones, quests, gems)

Loads JSON data files from Exile UI data format.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any


class GameDataLoader:
    """Loads and provides access to PoE game data"""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize data loader

        Args:
            data_dir: Path to data directory. Defaults to ../data/english/
        """
        if data_dir is None:
            # Default to data/english/ relative to this file
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent / "data" / "english"

        self.data_dir = Path(data_dir)

        # Lazy-loaded data
        self._areas: Optional[List[List[Dict[str, str]]]] = None
        self._guide: Optional[List[List[Any]]] = None
        self._gems: Optional[Dict[str, Any]] = None
        self._zone_name_map: Optional[Dict[str, Dict[str, str]]] = None
        self._zone_id_map: Optional[Dict[str, Dict[str, str]]] = None

    def _load_json(self, filename: str) -> Any:
        """Load a JSON file from data directory"""
        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @property
    def areas(self) -> List[List[Dict[str, str]]]:
        """
        Get all zone/area data

        Returns:
            List of acts, each containing list of zone objects
            Zone object: {"id": "1_1_1", "name": "Twilight Strand", "map_name": "..."}
        """
        if self._areas is None:
            self._areas = self._load_json("[leveltracker] areas.json")
        return self._areas

    @property
    def guide(self) -> List[List[Any]]:
        """
        Get leveling guide data

        Returns:
            List of acts, each containing list of guide steps
            Step can be: array of strings OR object with "condition" and "lines"
        """
        if self._guide is None:
            self._guide = self._load_json("[leveltracker] default guide.json")
        return self._guide

    @property
    def gems(self) -> Dict[str, Any]:
        """
        Get gem reward data

        Returns:
            Dict with "_quests" key and gem reward information
        """
        if self._gems is None:
            self._gems = self._load_json("[leveltracker] gems.json")
        return self._gems

    def get_act_areas(self, act: int) -> List[Dict[str, str]]:
        """
        Get all zones for a specific act

        Args:
            act: Act number (1-10)

        Returns:
            List of zone objects for that act
        """
        if act < 1 or act > len(self.areas):
            raise ValueError(f"Invalid act number: {act} (must be 1-{len(self.areas)})")

        return self.areas[act - 1]

    def get_act_guide(self, act: int) -> List[Any]:
        """
        Get leveling guide for a specific act

        Args:
            act: Act number (1-10)

        Returns:
            List of guide steps for that act
        """
        if act < 1 or act > len(self.guide):
            raise ValueError(f"Invalid act number: {act} (must be 1-{len(self.guide)})")

        return self.guide[act - 1]

    def find_zone_by_id(self, zone_id: str) -> Optional[Dict[str, str]]:
        """
        Find a zone by its unique ID

        Args:
            zone_id: Zone ID (e.g., "1_1_5", "1_3_8_1")

        Returns:
            Zone object if found, None otherwise
        """
        # Build lookup cache on first use
        if self._zone_id_map is None:
            self._zone_id_map = {}
            for act_zones in self.areas:
                for zone in act_zones:
                    self._zone_id_map[zone['id']] = zone

        return self._zone_id_map.get(zone_id)

    def find_zone_by_name(self, zone_name: str) -> Optional[Dict[str, str]]:
        """
        Find a zone by its name across all acts

        Args:
            zone_name: Zone name to search for

        Returns:
            Zone object if found, None otherwise
        """
        # Build lookup cache on first use
        if self._zone_name_map is None:
            self._zone_name_map = {}
            for act_zones in self.areas:
                for zone in act_zones:
                    self._zone_name_map[zone['name']] = zone
                    # Also index by map_name if it exists
                    if 'map_name' in zone:
                        self._zone_name_map[zone['map_name']] = zone

        return self._zone_name_map.get(zone_name)


def main():
    """Test the data loader"""
    print("=== Game Data Loader Test ===\n")

    loader = GameDataLoader()

    # Test areas
    print(f"Total acts (areas): {len(loader.areas)}")
    act1_zones = loader.get_act_areas(1)
    print(f"Act 1 zones: {len(act1_zones)}")
    print(f"First zone: {act1_zones[0]}")

    # Test guide
    print(f"\nTotal acts (guide): {len(loader.guide)}")
    act1_guide = loader.get_act_guide(1)
    print(f"Act 1 guide steps: {len(act1_guide)}")
    print(f"First step: {act1_guide[0]}")

    # Test gems
    print(f"\nGem data keys: {list(loader.gems.keys())[:5]}...")

    # Test zone lookup
    test_zone = "Lioneye's Watch"
    zone = loader.find_zone_by_name(test_zone)
    print(f"\nFound '{test_zone}': {zone}")

    print("\n✓ Data loader working!")


if __name__ == "__main__":
    main()
