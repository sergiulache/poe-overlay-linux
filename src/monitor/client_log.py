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

    # Common Steam library locations
    STEAM_PATHS = [
        "~/.steam/steam/steamapps/compatdata/238960/pfx/drive_c/Program Files (x86)/Grinding Gear Games/Path of Exile/logs/Client.txt",
        "~/.local/share/Steam/steamapps/compatdata/238960/pfx/drive_c/Program Files (x86)/Grinding Gear Games/Path of Exile/logs/Client.txt",
    ]

    # Regex patterns for log parsing
    ZONE_PATTERN = re.compile(r': Generating level \d+ area "([^"]+)"')

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
        # Try common Steam paths
        for path_template in self.STEAM_PATHS:
            path = Path(path_template).expanduser()
            if path.exists():
                return str(path)

        # TODO: Add Lutris/custom Wine prefix detection
        return None

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
        # Check for zone change
        match = self.ZONE_PATTERN.search(line)
        if match:
            zone_name = match.group(1)
            print(f"Zone detected: {zone_name}")
            for callback in self.callbacks['zone_change']:
                callback(zone_name)

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
