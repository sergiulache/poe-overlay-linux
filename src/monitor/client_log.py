#!/usr/bin/env python3
"""
Client.txt log file monitor for Path of Exile

Monitors PoE's Client.txt log file for game events (zone changes, etc.)
"""

import os
import time
import re
from pathlib import Path
from typing import Optional, Callable, List


class ClientLogMonitor:
    """Monitors PoE Client.txt for game events"""

    # Steam PoE app ID
    POE_APP_ID = "238960"

    # Regex patterns for log parsing
    # Pattern matches: ": You have entered <zone_name>."
    ZONE_PATTERN = re.compile(r': You have entered (.+)\.$')

    def __init__(self, client_txt_path: Optional[str] = None):
        """
        Initialize log monitor

        Args:
            client_txt_path: Path to Client.txt. If None, auto-detect.
        """
        self.client_txt_path = client_txt_path or self._find_client_txt()
        self.callbacks = {
            'zone_change': []
        }
        self._running = False
        self._last_position = 0

        if self.client_txt_path:
            print(f"Client.txt found: {self.client_txt_path}")
            # Start reading from end of file
            self._last_position = self._get_file_size()
        else:
            print("Warning: Client.txt not found. Monitor will not work.")

    def _find_client_txt(self) -> Optional[str]:
        """Auto-detect Client.txt location"""
        print("Searching for Client.txt...")

        # Check environment variable first
        env_path = os.environ.get('POE_CLIENT_TXT')
        if env_path:
            path = Path(env_path).expanduser()
            print(f"  Checking env var POE_CLIENT_TXT: {path}")
            if path.exists():
                print(f"  ✓ Found via environment variable")
                return str(path)
            else:
                print(f"  ✗ Path from environment variable doesn't exist")

        # Find Steam library folders from Steam config
        steam_libraries = self._find_steam_libraries()

        # Check each Steam library for PoE
        for library_path in steam_libraries:
            # Check common game install location
            poe_path = library_path / "steamapps" / "common" / "Path of Exile" / "logs" / "Client.txt"
            print(f"  Checking: {poe_path}")
            if poe_path.exists():
                print(f"  ✓ Found!")
                return str(poe_path)

            # Check Proton prefix location (for Windows build)
            prefix_path = library_path / "steamapps" / "compatdata" / self.POE_APP_ID / "pfx" / "drive_c" / "Program Files (x86)" / "Grinding Gear Games" / "Path of Exile" / "logs" / "Client.txt"
            print(f"  Checking: {prefix_path}")
            if prefix_path.exists():
                print(f"  ✓ Found!")
                return str(prefix_path)

        print("\n  ⚠ Client.txt not found in any Steam library")
        print("  Set POE_CLIENT_TXT environment variable to specify custom path:")
        print("    export POE_CLIENT_TXT='/path/to/Client.txt'")
        print("    ./run.sh")

        return None

    def _find_steam_libraries(self) -> List[Path]:
        """Find all Steam library folders by reading Steam config"""
        libraries = []

        # Standard Steam installation paths
        steam_roots = [
            Path.home() / ".steam" / "steam",
            Path.home() / ".local" / "share" / "Steam",
            # Flatpak Steam
            Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
        ]

        for steam_root in steam_roots:
            if not steam_root.exists():
                continue

            # Always include the main Steam folder
            libraries.append(steam_root)

            # Read libraryfolders.vdf to find additional Steam libraries
            vdf_path = steam_root / "steamapps" / "libraryfolders.vdf"
            if vdf_path.exists():
                print(f"  Reading Steam library config: {vdf_path}")
                try:
                    with open(vdf_path, 'r') as f:
                        content = f.read()
                        # Parse simple VDF format - look for "path" entries
                        import re
                        paths = re.findall(r'"path"\s+"([^"]+)"', content)
                        for path_str in paths:
                            lib_path = Path(path_str)
                            if lib_path.exists() and lib_path not in libraries:
                                libraries.append(lib_path)
                                print(f"    Found Steam library: {lib_path}")
                except Exception as e:
                    print(f"    Warning: Could not parse Steam config: {e}")

        return libraries

    def _get_file_size(self) -> int:
        """Get current file size"""
        if self.client_txt_path and os.path.exists(self.client_txt_path):
            return os.path.getsize(self.client_txt_path)
        return 0

    def on_zone_change(self, callback: Callable[[str], None]):
        """Register callback for zone change events"""
        self.callbacks['zone_change'].append(callback)

    def _parse_line(self, line: str):
        """Parse a log line and trigger callbacks"""
        # Debug: show what we're parsing
        if line.strip():  # Only show non-empty lines
            print(f"[DEBUG] Parsing: {line[:100]}")  # Show first 100 chars

        # Check for zone change
        match = self.ZONE_PATTERN.search(line)
        if match:
            zone_name = match.group(1)
            print(f"✓ Zone detected: {zone_name}")
            for callback in self.callbacks['zone_change']:
                callback(zone_name)
        elif "You have entered" in line or "Generating level" in line:
            # If line has zone-related keywords but didn't match, show why
            print(f"[DEBUG] Line looks like zone but didn't match pattern:")
            print(f"        Expected: ': You have entered <zone_name>.'")
            print(f"        Got: {line[:150]}")

    def start(self, poll_interval: float = 0.5):
        """
        Start monitoring the log file

        This is a blocking call - run in a background thread.

        Args:
            poll_interval: How often to check for new lines (seconds)
        """
        if not self.client_txt_path:
            print("Error: Cannot start monitor - Client.txt not found")
            return

        print(f"Starting Client.txt monitor (polling every {poll_interval}s)...")
        self._running = True

        with open(self.client_txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Seek to last read position
            f.seek(self._last_position)

            while self._running:
                line = f.readline()

                if line:
                    # Got a new line - process it
                    self._parse_line(line.strip())
                    self._last_position = f.tell()
                else:
                    # No new data - wait before checking again
                    time.sleep(poll_interval)

    def stop(self):
        """Stop monitoring"""
        print("Stopping Client.txt monitor...")
        self._running = False


def main():
    """Test the monitor with a sample Client.txt"""
    print("=== Client.txt Monitor Test ===\n")

    # Create monitor
    monitor = ClientLogMonitor()

    # Register callback
    def on_zone(zone_name: str):
        print(f"  → Zone callback fired: {zone_name}")

    monitor.on_zone_change(on_zone)

    # Start monitoring
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n\nStopping...")
        monitor.stop()


if __name__ == "__main__":
    main()
