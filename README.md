# PoE Overlay Linux

Native Linux overlay for Path of Exile leveling/progression tracking.

## Features

- **Act tracker** - Shows current zone, act, and progress
- **Passive points counter** - Tracks earned vs available passive points
- **Passive tree overlay** - Fullscreen click-through overlay for passive tree guidance
- **Wayland native** - Works on KDE Plasma and GNOME without XWayland

## Requirements

- Python 3.10+
- GTK4
- gtk4-layer-shell
- Wayland compositor (KDE/GNOME)

```bash
# Arch/CachyOS
sudo pacman -S python gtk4 gtk4-layer-shell
```

## Running

```bash
./run.sh
```

## Status

**MVP in progress** - Basic overlay working, Client.txt monitoring and data integration coming next.

## Credits

Game data (zones, quests, passive points) from [Exile UI](https://github.com/Lailloken/Exile-UI) by Lailloken.

Exile UI is an excellent AutoHotkey-based overlay for Windows. This project reimplements the leveling tracker for native Linux support.
