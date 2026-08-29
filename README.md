# Trova 🎬✨

[![Platform](https://img.shields.io/badge/Platform-Omarchy%20%7C%20Arch%20Linux-green.svg)](https://omarchy.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-ISC-purple.svg)](LICENSE)

**Trova** is a fast, keyboard-first cinema & streaming discovery companion engineered specifically for **[Omarchy Linux](https://omarchy.org)**.

Find where movies and TV shows are streaming worldwide across Netflix, Prime Video, Max, Paramount+, and regional services with instant country matrix intelligence, real-time Omarchy system theme synchronization, 1-click favorites, and native hardware-accelerated MPV playback.

---

## ⚡ 1-Line Quick Install

Copy and paste this single command into your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/visual-zimbabwe/trova/main/install.sh | bash
```

Once installed, launch Trova anytime via your application launcher or by running:
```bash
trova
```

> **Manual / Developer Installation**:
> ```bash
> git clone https://github.com/visual-zimbabwe/trova.git ~/apps/trova-app
> ~/apps/trova-app/install.sh
> ```

---

## ✨ Key Features

- 🎨 **Live Omarchy Theme Sync**: Automatically synchronizes with your active Omarchy system theme (`~/.local/state/omarchy/current/theme/colors.toml`) in real time (< 10ms) without page reloads.
- 🌍 **Global Streaming Availability**: Country-by-country streaming provider matrix for any film or series across 100+ countries with intelligent VPN exit detection.
- ⭐ **Simplified 1-Click Favorites**: 1-click starring (<kbd>F</kbd>) with automatic **Movies** and **TV Series** grouping, live home shelves, and an instant dedicated library view (<kbd>Shift+F</kbd>).
- 🎬 **Native MPV Trailer Player**: Stream official trailers directly in Omarchy's pre-configured, hardware-accelerated `mpv` player.
- 💻 **CLI Companion**: Search, roll random picks, stream trailers, and inspect cinema stats directly from your shell.
- ⚡ **Sub-Millisecond Cache**: Built-in SQLite caching ensures repeat queries and favorites render in under 1ms.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| <kbd>/</kbd> | Focus Search Bar |
| <kbd>0</kbd> | View All Streaming Services |
| <kbd>1</kbd> – <kbd>4</kbd> | Filter by Streaming Service (Netflix, Prime, Max, Paramount+) |
| <kbd>F</kbd> | Toggle Favorite (Star / Unstar title) |
| <kbd>Shift</kbd> + <kbd>F</kbd> | Open All Favorites Library View |
| <kbd>,</kbd> or <kbd>S</kbd> | Toggle Streaming Services Settings |
| <kbd>Esc</kbd> | Clear Search / Close Modal / Reset to Home |

---

## 💻 Terminal CLI Companion

Trova includes rich CLI utilities accessible straight from your shell:

```bash
trova search "Inception"      # Instant movie/TV search with year & media type
trova favs                    # List all favorites grouped by Movies & TV Series
trova stats                   # View cinema library analytics
trova play "Interstellar"     # Launch official trailer directly in MPV
trova random                  # Roll a random recommendation from your favorites
```

---

## 🧪 Running Tests

Run the full automated test suite (43 tests):

```bash
python3 -m pytest tests/ -v
```

---

## 📄 License

ISC License © 2026 Trova Contributors.
