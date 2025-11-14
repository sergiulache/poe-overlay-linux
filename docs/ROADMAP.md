# PoE Overlay Linux - Roadmap

## Current Status
✅ MVP overlay working on Wayland (KDE + GNOME)
✅ Click-through fullscreen overlay
✅ Corner overlay (always-on-top, no focus steal)

---

## Priority 1: Passive Tree Overlay

- [ ] Display passive tree image in fullscreen overlay
- [ ] Scale to different screen resolutions
- [ ] Handle zoom levels (game zooms passive tree)
- [ ] Handle different passive tree positions (game can move tree around)
- [ ] **Import from Path of Building (PoB)**
  - [ ] Parse PoB URLs/codes
  - [ ] Extract node order from build
  - [ ] Highlight next nodes to take
- [ ] Show node numbers/order on tree
- [ ] Support different build paths (respec support)

---

## Priority 2: Zone Guide (Quick Reference)

- [ ] Monitor Client.txt for zone changes
- [ ] Parse zone from log file
- [ ] Match zone to JSON data
- [ ] Display quick text guide:
  - Where to go in this zone
  - What to do (quest objectives, waypoints)
  - Layout hints
- [ ] Keep it minimal (2-3 lines max)
- [ ] Position in corner overlay or separate small box

---

## Other Features (No Priority Order)

### Core Functionality
- [ ] Client.txt log monitoring
- [ ] JSON data loading (zones, quests, gems)
- [ ] Detect PoE 1 vs PoE 2
- [ ] Auto-detect Client.txt location
- [ ] Handle multiple Steam library locations
- [ ] Handle Lutris/custom Wine prefixes

### Act/Zone Tracking
- [ ] Track current act
- [ ] Track quest completion
- [ ] Calculate passive points earned vs available
- [ ] Timer for speedruns (optional)
- [ ] Zone layout hints (images from assets/)

### Guides & Builds
- [ ] Load different leveling guides
- [ ] Switch guides with hotkey or button
- [ ] Multiple build profiles
- [ ] Gem recommendations per level
- [ ] Vendor recipe tracking

### UI/UX Polish
- [ ] Fix corner overlay styling delay
- [ ] Configurable overlay position
- [ ] Configurable overlay size
- [ ] Hide/show hotkey
- [ ] Transparency slider
- [ ] Theme customization

### Settings
- [ ] Settings panel/dialog
- [ ] Save user preferences
- [ ] Configure data paths
- [ ] Toggle features on/off

### Advanced
- [ ] Multiple monitor support
- [ ] Follow game window if moved
- [ ] Support for other Wayland compositors (Sway, Hyprland)
- [ ] Better GNOME Wayland support
- [ ] AppImage/Flatpak packaging
- [ ] Auto-update mechanism

---

## Tech Debt / Cleanup
- [ ] Split main.py into modules (overlay/corner.py, overlay/fullscreen.py)
- [ ] Move CSS to separate file (overlay/styles.py)
- [ ] Create data manager class
- [ ] Create log monitor class
- [ ] Add error handling
- [ ] Add logging
- [ ] Write tests
- [ ] Documentation for contributors

---

## Nice to Have
- [ ] Screenshot integration
- [ ] Build sharing (export/import builds)
- [ ] Community guide repository
- [ ] Translation support
- [ ] Stash tab helper
- [ ] Map tracker integration
- [ ] DPS calculator overlay
