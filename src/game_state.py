#!/usr/bin/env python3
"""
Game state integration - connects Client.txt monitoring to overlay UI

Wires together: Client.txt monitor → Zone tracker → UI callbacks
"""

import threading
from typing import Optional, Callable
from data_loader import GameDataLoader
from zone_tracker import ZoneTracker, ZoneEntry
from monitor.client_log import ClientLogMonitor


class GameState:
    """
    Manages game state and coordinates between monitor, tracker, and UI

    Starts Client.txt monitoring in background thread and provides
    thread-safe callbacks for UI updates.
    """

    def __init__(self, client_txt_path: Optional[str] = None):
        """
        Initialize game state manager

        Args:
            client_txt_path: Path to Client.txt. If None, auto-detect.
        """
        # Initialize components
        self.data_loader = GameDataLoader()
        self.tracker = ZoneTracker(self.data_loader)
        self.monitor = ClientLogMonitor(client_txt_path)

        # Monitor thread
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False

        # UI callbacks (set by UI code)
        self.on_zone_change: Optional[Callable[[ZoneEntry], None]] = None
        self.on_act_change: Optional[Callable[[int, int], None]] = None
        self.on_passive_point: Optional[Callable[[str, int], None]] = None

    def start(self):
        """
        Start monitoring Client.txt in background thread

        Connects monitor to tracker and sets up callbacks.
        """
        if self._running:
            print("GameState already running")
            return

        if not self.monitor.client_txt_path:
            print("Warning: Client.txt not found, monitoring disabled")
            return

        # Wire monitor to tracker
        def on_monitor_zone_change(zone_name: str):
            """Called by monitor when zone detected in log"""
            entry = self.tracker.enter_zone(zone_name)

            # Fire UI callback if set
            if entry and self.on_zone_change:
                self.on_zone_change(entry)

        self.monitor.on_zone_change(on_monitor_zone_change)

        # Wire tracker callbacks to UI callbacks
        def on_tracker_act_change(old_act: int, new_act: int):
            if self.on_act_change:
                self.on_act_change(old_act, new_act)

        def on_tracker_passive_point(zone_name: str, total: int):
            if self.on_passive_point:
                self.on_passive_point(zone_name, total)

        self.tracker.on_act_change(on_tracker_act_change)
        self.tracker.on_passive_point(on_tracker_passive_point)

        # Start monitor in background thread
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self.monitor.start,
            daemon=True,
            name="ClientLogMonitor"
        )
        self._monitor_thread.start()
        print("GameState monitoring started")

    def stop(self):
        """Stop monitoring"""
        if not self._running:
            return

        self._running = False
        self.monitor.stop()

        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None

        print("GameState monitoring stopped")

    def get_current_state(self) -> dict:
        """
        Get current game state snapshot

        Returns:
            Dict with current zone, act, passive points, etc.
        """
        return {
            'zone': self.tracker.current_zone.zone_name if self.tracker.current_zone else "Unknown",
            'act': self.tracker.current_act,
            'passive_points': self.tracker.passive_points,
            'zone_count': len(self.tracker.zone_history),
        }

    def reset(self):
        """Reset all tracking (new character/session)"""
        self.tracker.reset()
        print("GameState reset")


def main():
    """Test the game state integration"""
    print("=== Game State Integration Test ===\n")

    # Create game state
    game_state = GameState()

    # Register UI callbacks
    def on_zone(entry: ZoneEntry):
        print(f"  [UI] Zone: {entry.zone_name} (Act {entry.act})")

    def on_act(old_act: int, new_act: int):
        print(f"  [UI] Act changed: {old_act} → {new_act}")

    def on_passive(zone_name: str, total: int):
        print(f"  [UI] Passive point in {zone_name}! Total: {total}")

    game_state.on_zone_change = on_zone
    game_state.on_act_change = on_act
    game_state.on_passive_point = on_passive

    # Start monitoring
    print("Starting monitoring...\n")
    game_state.start()

    # Show current state
    import time
    time.sleep(1)

    state = game_state.get_current_state()
    print(f"\nCurrent state:")
    print(f"  Zone: {state['zone']}")
    print(f"  Act: {state['act']}")
    print(f"  Passive points: {state['passive_points']}")
    print(f"  Zones visited: {state['zone_count']}")

    print("\n✓ Integration working! Monitor for zone changes in Client.txt...")
    print("(Press Ctrl+C to stop)\n")

    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        game_state.stop()


if __name__ == "__main__":
    main()
