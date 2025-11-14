#!/usr/bin/env python3
"""
PoE Overlay - Wayland overlay for Path of Exile leveling tracking

Shows live zone, act, and passive point data from Client.txt monitoring.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell as LayerShell
import cairo
from game_state import GameState


class CornerOverlay(Gtk.Window):
    """Small corner overlay showing act progress"""

    # Class-level CSS provider
    _css_loaded = False

    def __init__(self, app, game_state):
        super().__init__(application=app)
        self.fullscreen_overlay = None
        self.game_state = game_state

        # Load CSS once for all instances
        if not CornerOverlay._css_loaded:
            self.load_css()
            CornerOverlay._css_loaded = True

        # Initialize layer shell
        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.OVERLAY)
        LayerShell.set_namespace(self, "poe-overlay")

        # Anchor to top-right corner
        LayerShell.set_anchor(self, LayerShell.Edge.TOP, True)
        LayerShell.set_anchor(self, LayerShell.Edge.RIGHT, True)

        # Set margins from edges
        LayerShell.set_margin(self, LayerShell.Edge.TOP, 10)
        LayerShell.set_margin(self, LayerShell.Edge.RIGHT, 10)

        # Don't steal keyboard focus from the game, but still accept mouse clicks
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.NONE)

        # Setup UI
        self.setup_ui()

    def load_css(self):
        """Load CSS globally"""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window {
                background-color: rgba(0, 0, 0, 0.85);
                color: white;
                border-radius: 8px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
            label {
                color: white;
                font-size: 13px;
            }
            .title-3 {
                font-weight: bold;
                font-size: 15px;
            }
            button {
                background-color: rgba(60, 60, 60, 0.9);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 28px;
            }
            button:hover {
                background-color: rgba(80, 80, 80, 0.9);
            }
        """)

        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display, css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_ui(self):
        """Create the UI elements"""
        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(15)
        box.set_margin_bottom(15)
        box.set_margin_start(15)
        box.set_margin_end(15)

        # Title
        title = Gtk.Label(label="PoE Leveling Tracker")
        title.add_css_class("title-3")
        box.append(title)

        # Game data (will update from callbacks)
        self.zone_label = Gtk.Label(label="Zone: Starting...")
        box.append(self.zone_label)

        self.act_label = Gtk.Label(label="Act: 1")
        box.append(self.act_label)

        self.points_label = Gtk.Label(label="Passive Points: 0")
        box.append(self.points_label)

        # Separator
        separator = Gtk.Separator()
        box.append(separator)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.passive_button = Gtk.Button(label="Passive Tree")
        self.passive_button.connect("clicked", self.on_passive_tree_clicked)
        button_box.append(self.passive_button)

        prev_button = Gtk.Button(label="◀")
        prev_button.connect("clicked", lambda b: print("Previous guide"))
        button_box.append(prev_button)

        next_button = Gtk.Button(label="▶")
        next_button.connect("clicked", lambda b: print("Next guide"))
        button_box.append(next_button)

        box.append(button_box)

        self.set_child(box)

        # Wire up game state callbacks
        self.setup_callbacks()

    def setup_callbacks(self):
        """Wire GameState callbacks to update UI"""
        def on_zone_change(entry):
            # Update UI from background thread safely
            GLib.idle_add(self.update_zone, entry.zone_name, entry.act)

        def on_act_change(old_act, new_act):
            GLib.idle_add(self.update_act, new_act)

        def on_passive_point(zone_name, total):
            GLib.idle_add(self.update_passive_points, total)

        self.game_state.on_zone_change = on_zone_change
        self.game_state.on_act_change = on_act_change
        self.game_state.on_passive_point = on_passive_point

    def update_zone(self, zone_name, act):
        """Update zone label (called from GTK main thread)"""
        self.zone_label.set_label(f"Zone: {zone_name}")
        self.act_label.set_label(f"Act: {act}")
        return False

    def update_act(self, act):
        """Update act label (called from GTK main thread)"""
        self.act_label.set_label(f"Act: {act}")
        return False

    def update_passive_points(self, total):
        """Update passive points label (called from GTK main thread)"""
        self.points_label.set_label(f"Passive Points: {total}")
        return False

    def on_passive_tree_clicked(self, button):
        """Toggle fullscreen passive tree overlay"""
        if self.fullscreen_overlay is None:
            self.fullscreen_overlay = FullscreenOverlay(self.get_application(), self)
            self.fullscreen_overlay.present()
            self.passive_button.set_label("Hide Tree")
        else:
            self.fullscreen_overlay.close()
            self.fullscreen_overlay = None
            self.passive_button.set_label("Passive Tree")


class FullscreenOverlay(Gtk.Window):
    """Fullscreen click-through overlay for passive tree"""

    def __init__(self, app, parent):
        super().__init__(application=app)
        self.parent_overlay = parent
        self.close_button = None

        # Initialize layer shell
        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.OVERLAY)
        LayerShell.set_namespace(self, "poe-overlay-fullscreen")

        # Fullscreen - anchor to all edges
        for edge in [LayerShell.Edge.TOP, LayerShell.Edge.BOTTOM,
                     LayerShell.Edge.LEFT, LayerShell.Edge.RIGHT]:
            LayerShell.set_anchor(self, edge, True)

        # Don't steal keyboard focus - this prevents the game from losing focus
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.NONE)

        # Setup UI first
        self.setup_ui()

        # Connect to map signal - fired after window is shown and layout is complete
        self.connect("map", self.on_map)

    def setup_ui(self):
        """Create the fullscreen UI"""
        # Overlay container
        overlay = Gtk.Overlay()

        # Main content (semi-transparent background)
        main_box = Gtk.Box()
        main_label = Gtk.Label(label="Passive Tree Overlay\n(Mock - would show tree image here)")
        main_label.set_justify(Gtk.Justification.CENTER)
        main_box.append(main_label)
        overlay.set_child(main_box)

        # Close button in top-left corner
        close_box = Gtk.Box()
        close_box.set_halign(Gtk.Align.START)
        close_box.set_valign(Gtk.Align.START)
        close_box.set_margin_top(10)
        close_box.set_margin_start(10)

        self.close_button = Gtk.Button(label="✕ Close")
        self.close_button.connect("clicked", self.on_close_clicked)
        close_box.append(self.close_button)

        overlay.add_overlay(close_box)

        # Add CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window {
                background-color: rgba(0, 0, 0, 0.5);
            }
            label {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
            button {
                background-color: rgba(200, 0, 0, 0.9);
                color: white;
                border: 2px solid white;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
            }
            button:hover {
                background-color: rgba(255, 0, 0, 0.9);
            }
        """)

        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display, css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.set_child(overlay)

    def on_map(self, widget):
        """Set input region after window is mapped to make it click-through except close button"""
        # Use idle_add to ensure layout is complete
        GLib.idle_add(self.set_input_region)

    def set_input_region(self):
        """Actually set the input region - called after layout is complete"""
        # Get the native surface
        surface = self.get_surface()
        if surface is None:
            print("Warning: Could not get surface for input region")
            return False

        # Get button size (GTK4 way)
        width = self.close_button.get_width()
        height = self.close_button.get_height()

        print(f"DEBUG: Button size: w={width}, h={height}")

        # Check if button is realized and has size
        if width == 0 or height == 0:
            print("Warning: Button not allocated yet, retrying...")
            # Try again in 100ms
            GLib.timeout_add(100, self.set_input_region)
            return False

        # Translate button coordinates to window coordinates
        coords = self.close_button.translate_coordinates(self, 0, 0)

        if coords is None:
            print("Warning: Could not translate coordinates, retrying...")
            GLib.timeout_add(100, self.set_input_region)
            return False

        x, y = coords
        print(f"DEBUG: Button position in window: x={x}, y={y}")

        # Create a cairo region with just the close button area
        # Add some padding to make it easier to click
        padding = 10
        region = cairo.Region(cairo.RectangleInt(
            max(0, int(x) - padding),
            max(0, int(y) - padding),
            width + (padding * 2),
            height + (padding * 2)
        ))

        # Set the input region - only this area will receive input
        surface.set_input_region(region)
        print(f"Input region set to close button (with padding): x={int(x)-padding}, y={int(y)-padding}, w={width+padding*2}, h={height+padding*2}")

        # Force the surface to queue a frame - this commits the input region changes
        surface.queue_render()

        # Also request a frame callback to ensure compositor processes it
        self.queue_draw()

        # Return False so idle_add doesn't call this again
        return False

    def on_close_clicked(self, button):
        """Close the fullscreen overlay"""
        self.parent_overlay.fullscreen_overlay = None
        self.parent_overlay.passive_button.set_label("Passive Tree")
        self.close()


class OverlayApp(Gtk.Application):
    """Main application"""

    def __init__(self):
        super().__init__(application_id="com.poe.overlay.test")
        self.game_state = None

    def do_activate(self):
        """Application activation"""
        if not self.get_windows():
            # Initialize game state
            print("Initializing game state...")
            self.game_state = GameState()
            self.game_state.start()

            # Create and show overlay
            corner = CornerOverlay(self, self.game_state)
            corner.present()

            print("Overlay started and monitoring Client.txt")

    def do_shutdown(self):
        """Application shutdown"""
        if self.game_state:
            print("Stopping game state monitoring...")
            self.game_state.stop()
        super().do_shutdown()


def main():
    """Entry point"""
    print("Starting PoE Overlay Test...")
    print("Platform:", GLib.get_os_info("PRETTY_NAME") or "Unknown")

    app = OverlayApp()
    return app.run(None)


if __name__ == "__main__":
    exit(main())
